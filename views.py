"""
Leads Module Views

Pipeline and lead management: dashboard, Kanban pipeline, lead list, settings.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render as django_render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    Pipeline, PipelineStage, LossReason, Lead, LeadActivity,
    LeadSettings, ensure_default_pipeline,
    SOURCE_CHOICES, PRIORITY_CHOICES,
)
from .forms import (
    LeadForm, PipelineForm, PipelineStageForm,
    LossReasonForm, LeadSettingsForm, LeadActivityForm, LeadLostForm,
)


# ============================================================================
# Constants
# ============================================================================

LEAD_SORT_FIELDS = {
    'name': 'name',
    'company': 'company',
    'value': 'value',
    'priority': 'priority',
    'stage': 'stage__order',
    'created': 'created_at',
    'expected_close': 'expected_close_date',
}

PER_PAGE_CHOICES = [10, 25, 50, 100]


def _hub_id(request):
    return request.session.get('hub_id')


def _ensure_pipeline(hub_id):
    """Ensure a default pipeline exists for the hub."""
    return ensure_default_pipeline(hub_id)


def _render_leads_list(request, hub_id, per_page=10):
    """Render the leads list partial after a mutation."""
    pipeline = _ensure_pipeline(hub_id)
    leads = Lead.objects.filter(
        hub_id=hub_id, is_deleted=False, status='open',
    ).select_related('pipeline', 'stage').order_by('-created_at')
    paginator = Paginator(leads, per_page)
    page_obj = paginator.get_page(1)
    stages = PipelineStage.objects.filter(
        hub_id=hub_id, pipeline=pipeline, is_deleted=False,
    ).order_by('order')
    return django_render(request, 'leads/partials/leads_list.html', {
        'leads': page_obj,
        'page_obj': page_obj,
        'search_query': '',
        'sort_field': 'created',
        'sort_dir': 'desc',
        'stage_filter': '',
        'source_filter': '',
        'priority_filter': '',
        'status_filter': 'open',
        'stages_list': stages,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'per_page': per_page,
    })


# ============================================================================
# Dashboard
# ============================================================================

@login_required
@with_module_nav('leads', 'dashboard')
@htmx_view('leads/pages/dashboard.html', 'leads/partials/dashboard_content.html')
def dashboard(request):
    """Leads dashboard with key metrics."""
    hub = _hub_id(request)
    _ensure_pipeline(hub)

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total open leads
    open_leads = Lead.objects.filter(
        hub_id=hub, is_deleted=False, status='open',
    )
    total_open = open_leads.count()
    pipeline_value = open_leads.aggregate(
        total=Sum('value')
    )['total'] or Decimal('0.00')

    # Won this month
    won_this_month = Lead.objects.filter(
        hub_id=hub, is_deleted=False, status='won',
        won_date__gte=month_start,
    )
    won_count = won_this_month.count()
    won_value = won_this_month.aggregate(
        total=Sum('value')
    )['total'] or Decimal('0.00')

    # Lost this month
    lost_this_month = Lead.objects.filter(
        hub_id=hub, is_deleted=False, status='lost',
        lost_date__gte=month_start,
    )
    lost_count = lost_this_month.count()

    # Conversion rate (this month: won / (won + lost))
    total_closed = won_count + lost_count
    conversion_rate = round((won_count / total_closed * 100), 1) if total_closed > 0 else 0

    # Average close time (days) for won leads
    won_leads_with_dates = Lead.objects.filter(
        hub_id=hub, is_deleted=False, status='won',
        won_date__isnull=False,
    )
    if won_leads_with_dates.exists():
        # Calculate average days manually
        total_days = 0
        count = 0
        for lead in won_leads_with_dates[:100]:  # Limit for performance
            delta = lead.won_date - lead.created_at
            total_days += delta.days
            count += 1
        avg_close_days = round(total_days / count) if count > 0 else 0
    else:
        avg_close_days = 0

    # Recent leads
    recent_leads = Lead.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('pipeline', 'stage').order_by('-created_at')[:5]

    # Recent activities
    recent_activities = LeadActivity.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('lead').order_by('-created_at')[:10]

    # Pipeline breakdown (leads per stage)
    default_pipeline = Pipeline.objects.filter(
        hub_id=hub, is_deleted=False, is_default=True,
    ).first() or Pipeline.objects.filter(
        hub_id=hub, is_deleted=False,
    ).first()

    stage_breakdown = []
    if default_pipeline:
        stages = default_pipeline.stages.filter(
            is_deleted=False,
        ).order_by('order')
        for stage in stages:
            stage_leads = Lead.objects.filter(
                hub_id=hub, is_deleted=False, status='open',
                stage=stage,
            )
            stage_breakdown.append({
                'stage': stage,
                'count': stage_leads.count(),
                'value': stage_leads.aggregate(total=Sum('value'))['total'] or Decimal('0.00'),
            })

    return {
        'total_open': total_open,
        'pipeline_value': pipeline_value,
        'won_count': won_count,
        'won_value': won_value,
        'lost_count': lost_count,
        'conversion_rate': conversion_rate,
        'avg_close_days': avg_close_days,
        'recent_leads': recent_leads,
        'recent_activities': recent_activities,
        'stage_breakdown': stage_breakdown,
    }


# ============================================================================
# Pipeline (Kanban)
# ============================================================================

@login_required
@with_module_nav('leads', 'pipeline')
@htmx_view('leads/pages/pipeline.html', 'leads/partials/pipeline_content.html')
def pipeline(request):
    """Pipeline Kanban view."""
    hub = _hub_id(request)
    default_pipeline = _ensure_pipeline(hub)

    pipeline_id = request.GET.get('pipeline')
    if pipeline_id:
        current_pipeline = get_object_or_404(
            Pipeline, id=pipeline_id, hub_id=hub, is_deleted=False,
        )
    else:
        current_pipeline = Pipeline.objects.filter(
            hub_id=hub, is_deleted=False, is_default=True,
        ).first() or default_pipeline

    pipelines = Pipeline.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('-is_default', 'name')

    # Get stages with their open leads
    stages = current_pipeline.stages.filter(
        is_deleted=False, is_won=False, is_lost=False,
    ).order_by('order')

    stage_data = []
    for stage in stages:
        leads = Lead.objects.filter(
            hub_id=hub, is_deleted=False, status='open',
            stage=stage,
        ).select_related('pipeline', 'stage').order_by('-value', '-created_at')
        stage_data.append({
            'stage': stage,
            'leads': leads,
            'count': leads.count(),
            'value': leads.aggregate(total=Sum('value'))['total'] or Decimal('0.00'),
        })

    return {
        'current_pipeline': current_pipeline,
        'pipelines': pipelines,
        'stage_data': stage_data,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
    }


# ============================================================================
# Leads List (Datatable)
# ============================================================================

@login_required
@with_module_nav('leads', 'list')
@htmx_view('leads/pages/list.html', 'leads/partials/leads_content.html')
def lead_list(request):
    """Leads list with search, sort, filter, pagination."""
    hub = _hub_id(request)
    _ensure_pipeline(hub)

    search_query = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'created')
    sort_dir = request.GET.get('dir', 'desc')
    stage_filter = request.GET.get('stage', '')
    source_filter = request.GET.get('source', '')
    priority_filter = request.GET.get('priority', '')
    status_filter = request.GET.get('status', 'open')
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    leads = Lead.objects.filter(hub_id=hub, is_deleted=False).select_related(
        'pipeline', 'stage', 'customer', 'loss_reason',
    )

    # Status filter
    if status_filter and status_filter != 'all':
        leads = leads.filter(status=status_filter)

    # Search
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(company__icontains=search_query)
        )

    # Stage filter
    if stage_filter:
        leads = leads.filter(stage_id=stage_filter)

    # Source filter
    if source_filter:
        leads = leads.filter(source=source_filter)

    # Priority filter
    if priority_filter:
        leads = leads.filter(priority=priority_filter)

    # Sort
    order_by = LEAD_SORT_FIELDS.get(sort_field, 'created_at')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    leads = leads.order_by(order_by)

    # Pagination
    paginator = Paginator(leads, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Get filter options
    default_pipeline = Pipeline.objects.filter(
        hub_id=hub, is_deleted=False, is_default=True,
    ).first() or Pipeline.objects.filter(
        hub_id=hub, is_deleted=False,
    ).first()

    stages_list = PipelineStage.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('order') if default_pipeline else []

    context = {
        'leads': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'stage_filter': stage_filter,
        'source_filter': source_filter,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
        'stages_list': stages_list,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'per_page': per_page,
    }

    # HTMX partial: swap only datatable body
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'datatable-body':
        return django_render(request, 'leads/partials/leads_list.html', context)

    return context


# ============================================================================
# Lead CRUD
# ============================================================================

@login_required
def lead_add(request):
    """Add lead - renders in side panel via HTMX."""
    hub = _hub_id(request)
    default_pipeline = _ensure_pipeline(hub)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, _('Name is required'))
            stages = PipelineStage.objects.filter(
                hub_id=hub, pipeline=default_pipeline, is_deleted=False,
                is_won=False, is_lost=False,
            ).order_by('order')
            pipelines = Pipeline.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
            return django_render(request, 'leads/partials/panel_lead_add.html', {
                'pipelines': pipelines,
                'stages': stages,
                'source_choices': SOURCE_CHOICES,
                'priority_choices': PRIORITY_CHOICES,
                'default_pipeline': default_pipeline,
            })

        # Get pipeline and stage
        pipeline_id = request.POST.get('pipeline')
        stage_id = request.POST.get('stage')

        if pipeline_id:
            lead_pipeline = get_object_or_404(
                Pipeline, id=pipeline_id, hub_id=hub, is_deleted=False,
            )
        else:
            lead_pipeline = default_pipeline

        if stage_id:
            lead_stage = get_object_or_404(
                PipelineStage, id=stage_id, hub_id=hub, is_deleted=False,
            )
        else:
            lead_stage = lead_pipeline.stages.filter(
                is_deleted=False, is_won=False, is_lost=False,
            ).order_by('order').first()

        if not lead_stage:
            messages.error(request, _('No stages available in this pipeline'))
            return _render_leads_list(request, hub)

        # Get customer if provided
        customer_id = request.POST.get('customer')
        customer = None
        if customer_id:
            try:
                from customers.models import Customer
                customer = Customer.objects.filter(
                    id=customer_id, hub_id=hub, is_deleted=False,
                ).first()
            except (ImportError, Exception):
                pass

        lead = Lead.objects.create(
            hub_id=hub,
            name=name,
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            company=request.POST.get('company', '').strip(),
            value=request.POST.get('value', '0') or '0',
            expected_close_date=request.POST.get('expected_close_date') or None,
            pipeline=lead_pipeline,
            stage=lead_stage,
            source=request.POST.get('source', 'manual'),
            priority=request.POST.get('priority', 'medium'),
            notes=request.POST.get('notes', '').strip(),
            customer=customer,
        )

        # Log creation activity
        LeadActivity.objects.create(
            hub_id=hub,
            lead=lead,
            activity_type='note',
            description=str(_('Lead created')),
            metadata={'source': lead.source},
        )

        messages.success(request, _('Lead added successfully'))
        return _render_leads_list(request, hub)

    # GET - render add form
    pipelines = Pipeline.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    stages = PipelineStage.objects.filter(
        hub_id=hub, pipeline=default_pipeline, is_deleted=False,
        is_won=False, is_lost=False,
    ).order_by('order')

    # Get settings for defaults
    settings = LeadSettings.get_settings(hub)

    # Get customers for dropdown
    customers_list = []
    try:
        from customers.models import Customer
        customers_list = Customer.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        ).order_by('name')[:100]
    except (ImportError, Exception):
        pass

    return django_render(request, 'leads/partials/panel_lead_add.html', {
        'pipelines': pipelines,
        'stages': stages,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'default_pipeline': default_pipeline,
        'default_source': settings.default_source,
        'customers_list': customers_list,
    })


@login_required
def lead_edit(request, lead_id):
    """Edit lead - renders in side panel via HTMX."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, _('Name is required'))
            pipelines = Pipeline.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
            stages = PipelineStage.objects.filter(
                hub_id=hub, pipeline=lead.pipeline, is_deleted=False,
                is_won=False, is_lost=False,
            ).order_by('order')
            return django_render(request, 'leads/partials/panel_lead_edit.html', {
                'lead': lead,
                'pipelines': pipelines,
                'stages': stages,
                'source_choices': SOURCE_CHOICES,
                'priority_choices': PRIORITY_CHOICES,
            })

        lead.name = name
        lead.email = request.POST.get('email', '').strip()
        lead.phone = request.POST.get('phone', '').strip()
        lead.company = request.POST.get('company', '').strip()
        lead.value = request.POST.get('value', '0') or '0'
        lead.expected_close_date = request.POST.get('expected_close_date') or None
        lead.source = request.POST.get('source', 'manual')
        lead.priority = request.POST.get('priority', 'medium')
        lead.notes = request.POST.get('notes', '').strip()

        # Handle stage change
        new_stage_id = request.POST.get('stage')
        if new_stage_id and str(lead.stage_id) != new_stage_id:
            new_stage = get_object_or_404(
                PipelineStage, id=new_stage_id, hub_id=hub, is_deleted=False,
            )
            lead.move_to_stage(new_stage)

        # Handle customer
        customer_id = request.POST.get('customer')
        if customer_id:
            try:
                from customers.models import Customer
                lead.customer = Customer.objects.filter(
                    id=customer_id, hub_id=hub, is_deleted=False,
                ).first()
            except (ImportError, Exception):
                pass
        else:
            lead.customer = None

        lead.save()

        messages.success(request, _('Lead updated successfully'))
        return _render_leads_list(request, hub)

    # GET - render edit form
    pipelines = Pipeline.objects.filter(hub_id=hub, is_deleted=False, is_active=True)
    stages = PipelineStage.objects.filter(
        hub_id=hub, pipeline=lead.pipeline, is_deleted=False,
        is_won=False, is_lost=False,
    ).order_by('order')

    customers_list = []
    try:
        from customers.models import Customer
        customers_list = Customer.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        ).order_by('name')[:100]
    except (ImportError, Exception):
        pass

    return django_render(request, 'leads/partials/panel_lead_edit.html', {
        'lead': lead,
        'pipelines': pipelines,
        'stages': stages,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'customers_list': customers_list,
    })


@login_required
@with_module_nav('leads', 'list')
@htmx_view('leads/pages/list.html', 'leads/partials/lead_detail.html')
def lead_detail(request, lead_id):
    """Lead detail view with activity timeline."""
    hub = _hub_id(request)
    lead = get_object_or_404(
        Lead, id=lead_id, hub_id=hub, is_deleted=False,
    )
    lead_obj = Lead.objects.select_related(
        'pipeline', 'stage', 'customer', 'loss_reason',
    ).get(pk=lead.pk)

    activities = LeadActivity.objects.filter(
        hub_id=hub, lead=lead, is_deleted=False,
    ).order_by('-created_at')[:50]

    loss_reasons = LossReason.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')

    stages = PipelineStage.objects.filter(
        hub_id=hub, pipeline=lead.pipeline, is_deleted=False,
        is_won=False, is_lost=False,
    ).order_by('order')

    return {
        'lead': lead_obj,
        'activities': activities,
        'loss_reasons': loss_reasons,
        'stages': stages,
        'source_choices': SOURCE_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
    }


@login_required
@require_POST
def lead_delete(request, lead_id):
    """Soft delete lead."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)
    lead.is_deleted = True
    lead.deleted_at = timezone.now()
    lead.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    messages.success(request, _('Lead deleted successfully'))
    return _render_leads_list(request, hub)


# ============================================================================
# Lead Stage Move (Kanban drag-and-drop)
# ============================================================================

@login_required
@require_POST
def lead_move_stage(request, lead_id):
    """Move lead to a different stage (from Kanban drag-and-drop)."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    stage_id = request.POST.get('stage_id')
    if not stage_id:
        return JsonResponse({'success': False, 'error': 'stage_id required'}, status=400)

    new_stage = get_object_or_404(
        PipelineStage, id=stage_id, hub_id=hub, is_deleted=False,
    )

    if str(lead.stage_id) != str(stage_id):
        lead.move_to_stage(new_stage)

    return JsonResponse({
        'success': True,
        'lead_id': str(lead.id),
        'new_stage_id': str(new_stage.id),
        'status': lead.status,
    })


# ============================================================================
# Lead Won/Lost
# ============================================================================

@login_required
@require_POST
def lead_won(request, lead_id):
    """Mark lead as won."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    lead.mark_won()

    # Auto-create customer if setting enabled
    settings = LeadSettings.get_settings(hub)
    if settings.auto_create_customer_on_win and not lead.customer:
        customer = lead.convert_to_customer()
        if customer:
            messages.info(request, _('Customer "%(name)s" created from lead') % {
                'name': customer.name,
            })

    messages.success(request, _('Lead marked as won'))

    # Return appropriate response
    if request.headers.get('HX-Request'):
        return _render_leads_list(request, hub)
    return JsonResponse({'success': True, 'status': 'won'})


@login_required
@require_POST
def lead_lost(request, lead_id):
    """Mark lead as lost."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    loss_reason_id = request.POST.get('loss_reason')
    loss_reason = None
    if loss_reason_id:
        loss_reason = LossReason.objects.filter(
            id=loss_reason_id, hub_id=hub, is_deleted=False,
        ).first()

    lead.mark_lost(loss_reason)

    messages.success(request, _('Lead marked as lost'))

    if request.headers.get('HX-Request'):
        return _render_leads_list(request, hub)
    return JsonResponse({'success': True, 'status': 'lost'})


# ============================================================================
# Lead Convert
# ============================================================================

@login_required
@require_POST
def lead_convert(request, lead_id):
    """Convert lead to customer."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    if lead.customer:
        messages.warning(request, _('This lead already has a customer linked'))
    else:
        customer = lead.convert_to_customer()
        if customer:
            messages.success(request, _('Customer "%(name)s" created from lead') % {
                'name': customer.name,
            })
        else:
            messages.error(request, _('Failed to create customer. Is the customers module active?'))

    if request.headers.get('HX-Request'):
        return _render_leads_list(request, hub)
    return JsonResponse({'success': True})


# ============================================================================
# Lead Activity
# ============================================================================

@login_required
@require_POST
def lead_add_activity(request, lead_id):
    """Add an activity to a lead."""
    hub = _hub_id(request)
    lead = get_object_or_404(Lead, id=lead_id, hub_id=hub, is_deleted=False)

    activity_type = request.POST.get('activity_type', 'note')
    description = request.POST.get('description', '').strip()

    if not description:
        messages.error(request, _('Description is required'))
        if request.headers.get('HX-Request'):
            activities = LeadActivity.objects.filter(
                hub_id=hub, lead=lead, is_deleted=False,
            ).order_by('-created_at')[:50]
            return django_render(request, 'leads/partials/lead_detail.html', {
                'lead': lead,
                'activities': activities,
            })
        return JsonResponse({'success': False, 'error': 'description required'}, status=400)

    LeadActivity.objects.create(
        hub_id=hub,
        lead=lead,
        activity_type=activity_type,
        description=description,
    )

    messages.success(request, _('Activity added'))

    if request.headers.get('HX-Request'):
        # Re-render the lead detail
        lead_obj = Lead.objects.select_related(
            'pipeline', 'stage', 'customer', 'loss_reason',
        ).get(pk=lead.pk)
        activities = LeadActivity.objects.filter(
            hub_id=hub, lead=lead, is_deleted=False,
        ).order_by('-created_at')[:50]
        loss_reasons = LossReason.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        ).order_by('sort_order', 'name')
        stages = PipelineStage.objects.filter(
            hub_id=hub, pipeline=lead.pipeline, is_deleted=False,
            is_won=False, is_lost=False,
        ).order_by('order')
        return django_render(request, 'leads/partials/lead_detail.html', {
            'lead': lead_obj,
            'activities': activities,
            'loss_reasons': loss_reasons,
            'stages': stages,
            'source_choices': SOURCE_CHOICES,
            'priority_choices': PRIORITY_CHOICES,
        })
    return JsonResponse({'success': True})


# ============================================================================
# Settings
# ============================================================================

@login_required
@with_module_nav('leads', 'settings')
@htmx_view('leads/pages/settings.html', 'leads/partials/settings_content.html')
def settings_view(request):
    """Leads module settings."""
    hub = _hub_id(request)
    _ensure_pipeline(hub)

    settings = LeadSettings.get_settings(hub)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'save_settings':
            # Update settings
            default_pipeline_id = request.POST.get('default_pipeline')
            if default_pipeline_id:
                settings.default_pipeline = Pipeline.objects.filter(
                    id=default_pipeline_id, hub_id=hub, is_deleted=False,
                ).first()
            settings.auto_create_customer_on_win = request.POST.get('auto_create_customer_on_win') == 'on'
            settings.default_source = request.POST.get('default_source', 'manual')
            settings.save()
            messages.success(request, _('Settings saved'))

        elif action == 'add_stage':
            pipeline_id = request.POST.get('pipeline_id')
            pipeline_obj = get_object_or_404(
                Pipeline, id=pipeline_id, hub_id=hub, is_deleted=False,
            )
            name = request.POST.get('stage_name', '').strip()
            if name:
                max_order = pipeline_obj.stages.filter(
                    is_deleted=False,
                ).aggregate(max_order=models.Max('order'))['max_order'] or 0
                PipelineStage.objects.create(
                    hub_id=hub,
                    pipeline=pipeline_obj,
                    name=name,
                    order=max_order + 10,
                    probability=int(request.POST.get('stage_probability', 0) or 0),
                    color=request.POST.get('stage_color', 'primary'),
                    is_won=request.POST.get('stage_is_won') == 'on',
                    is_lost=request.POST.get('stage_is_lost') == 'on',
                )
                messages.success(request, _('Stage added'))

        elif action == 'delete_stage':
            stage_id = request.POST.get('stage_id')
            stage = get_object_or_404(
                PipelineStage, id=stage_id, hub_id=hub, is_deleted=False,
            )
            # Check if any leads are in this stage
            leads_in_stage = Lead.objects.filter(
                hub_id=hub, stage=stage, is_deleted=False, status='open',
            ).count()
            if leads_in_stage > 0:
                messages.error(request, _('Cannot delete stage with %(count)d active leads') % {
                    'count': leads_in_stage,
                })
            else:
                stage.is_deleted = True
                stage.deleted_at = timezone.now()
                stage.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
                messages.success(request, _('Stage deleted'))

        elif action == 'add_pipeline':
            name = request.POST.get('pipeline_name', '').strip()
            if name:
                Pipeline.objects.create(
                    hub_id=hub,
                    name=name,
                    description=request.POST.get('pipeline_description', '').strip(),
                )
                messages.success(request, _('Pipeline added'))

        elif action == 'add_loss_reason':
            name = request.POST.get('reason_name', '').strip()
            if name:
                max_order = LossReason.objects.filter(
                    hub_id=hub, is_deleted=False,
                ).aggregate(max_order=models.Max('sort_order'))['max_order'] or 0
                LossReason.objects.create(
                    hub_id=hub,
                    name=name,
                    sort_order=max_order + 10,
                )
                messages.success(request, _('Loss reason added'))

        elif action == 'delete_loss_reason':
            reason_id = request.POST.get('reason_id')
            reason = get_object_or_404(
                LossReason, id=reason_id, hub_id=hub, is_deleted=False,
            )
            reason.is_deleted = True
            reason.deleted_at = timezone.now()
            reason.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
            messages.success(request, _('Loss reason deleted'))

    # Build context
    pipelines = Pipeline.objects.filter(
        hub_id=hub, is_deleted=False,
    ).prefetch_related('stages').order_by('-is_default', 'name')

    loss_reasons = LossReason.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('sort_order', 'name')

    total_leads = Lead.objects.filter(hub_id=hub, is_deleted=False).count()
    open_leads = Lead.objects.filter(hub_id=hub, is_deleted=False, status='open').count()
    won_leads = Lead.objects.filter(hub_id=hub, is_deleted=False, status='won').count()
    lost_leads = Lead.objects.filter(hub_id=hub, is_deleted=False, status='lost').count()

    return {
        'settings': settings,
        'pipelines': pipelines,
        'loss_reasons': loss_reasons,
        'source_choices': SOURCE_CHOICES,
        'stage_colors': [
            ('primary', _('Primary')),
            ('secondary', _('Secondary')),
            ('success', _('Success')),
            ('warning', _('Warning')),
            ('danger', _('Danger')),
            ('info', _('Info')),
        ],
        'total_leads': total_leads,
        'open_leads': open_leads,
        'won_leads': won_leads,
        'lost_leads': lost_leads,
    }


# ============================================================================
# Pipeline Data API (JSON for Alpine.js Kanban)
# ============================================================================

@login_required
@require_http_methods(["GET"])
def pipeline_data_api(request):
    """Return pipeline data as JSON for the Kanban board."""
    hub = _hub_id(request)
    _ensure_pipeline(hub)

    pipeline_id = request.GET.get('pipeline')
    if pipeline_id:
        current_pipeline = get_object_or_404(
            Pipeline, id=pipeline_id, hub_id=hub, is_deleted=False,
        )
    else:
        current_pipeline = Pipeline.objects.filter(
            hub_id=hub, is_deleted=False, is_default=True,
        ).first() or Pipeline.objects.filter(
            hub_id=hub, is_deleted=False,
        ).first()

    if not current_pipeline:
        return JsonResponse({'success': False, 'error': 'No pipeline found'}, status=404)

    stages = current_pipeline.stages.filter(
        is_deleted=False, is_won=False, is_lost=False,
    ).order_by('order')

    data = {
        'success': True,
        'pipeline': {
            'id': str(current_pipeline.id),
            'name': current_pipeline.name,
        },
        'stages': [],
    }

    for stage in stages:
        leads = Lead.objects.filter(
            hub_id=hub, is_deleted=False, status='open',
            stage=stage,
        ).order_by('-value', '-created_at')

        stage_data = {
            'id': str(stage.id),
            'name': stage.name,
            'color': stage.color,
            'probability': stage.probability,
            'order': stage.order,
            'leads': [],
        }

        for lead in leads:
            stage_data['leads'].append({
                'id': str(lead.id),
                'name': lead.name,
                'company': lead.company,
                'value': float(lead.value),
                'priority': lead.priority,
                'priority_color': lead.priority_color,
                'source': lead.source,
                'days_in_stage': lead.days_in_stage,
                'initials': lead.initials,
                'email': lead.email,
                'phone': lead.phone,
            })

        data['stages'].append(stage_data)

    return JsonResponse(data)
