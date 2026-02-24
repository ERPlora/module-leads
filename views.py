"""
Leads Module Views
"""
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render as django_render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.core.services import export_to_csv, export_to_excel
from apps.modules_runtime.navigation import with_module_nav

from .models import Pipeline, PipelineStage, LossReason, Lead, LeadActivity, LeadSettings

PER_PAGE_CHOICES = [10, 25, 50, 100]


# ======================================================================
# Dashboard
# ======================================================================

@login_required
@with_module_nav('leads', 'dashboard')
@htmx_view('leads/pages/index.html', 'leads/partials/dashboard_content.html')
def dashboard(request):
    hub_id = request.session.get('hub_id')
    return {
        'total_pipelines': Pipeline.objects.filter(hub_id=hub_id, is_deleted=False).count(),
        'total_loss_reasons': LossReason.objects.filter(hub_id=hub_id, is_deleted=False).count(),
    }


# ======================================================================
# Pipeline
# ======================================================================

PIPELINE_SORT_FIELDS = {
    'name': 'name',
    'is_default': 'is_default',
    'is_active': 'is_active',
    'description': 'description',
    'created_at': 'created_at',
}

def _build_pipelines_context(hub_id, per_page=10):
    qs = Pipeline.objects.filter(hub_id=hub_id, is_deleted=False).order_by('name')
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(1)
    return {
        'pipelines': page_obj,
        'page_obj': page_obj,
        'search_query': '',
        'sort_field': 'name',
        'sort_dir': 'asc',
        'current_view': 'table',
        'per_page': per_page,
    }

def _render_pipelines_list(request, hub_id, per_page=10):
    ctx = _build_pipelines_context(hub_id, per_page)
    return django_render(request, 'leads/partials/pipelines_list.html', ctx)

@login_required
@with_module_nav('leads', 'pipeline')
@htmx_view('leads/pages/pipelines.html', 'leads/partials/pipelines_content.html')
def pipelines_list(request):
    hub_id = request.session.get('hub_id')
    search_query = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir', 'asc')
    page_number = request.GET.get('page', 1)
    current_view = request.GET.get('view', 'table')
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    qs = Pipeline.objects.filter(hub_id=hub_id, is_deleted=False)

    if search_query:
        qs = qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    order_by = PIPELINE_SORT_FIELDS.get(sort_field, 'name')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    qs = qs.order_by(order_by)

    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        fields = ['name', 'is_default', 'is_active', 'description']
        headers = ['Name', 'Is Default', 'Is Active', 'Description']
        if export_format == 'csv':
            return export_to_csv(qs, fields=fields, headers=headers, filename='pipelines.csv')
        return export_to_excel(qs, fields=fields, headers=headers, filename='pipelines.xlsx')

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'leads/partials/pipelines_list.html', {
            'pipelines': page_obj, 'page_obj': page_obj,
            'search_query': search_query, 'sort_field': sort_field,
            'sort_dir': sort_dir, 'current_view': current_view, 'per_page': per_page,
        })

    return {
        'pipelines': page_obj, 'page_obj': page_obj,
        'search_query': search_query, 'sort_field': sort_field,
        'sort_dir': sort_dir, 'current_view': current_view, 'per_page': per_page,
    }

@login_required
def pipeline_add(request):
    hub_id = request.session.get('hub_id')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_default = request.POST.get('is_default') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        obj = Pipeline(hub_id=hub_id)
        obj.name = name
        obj.description = description
        obj.is_default = is_default
        obj.is_active = is_active
        obj.save()
        return _render_pipelines_list(request, hub_id)
    return django_render(request, 'leads/partials/panel_pipeline_add.html', {})

@login_required
def pipeline_edit(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(Pipeline, pk=pk, hub_id=hub_id, is_deleted=False)
    if request.method == 'POST':
        obj.name = request.POST.get('name', '').strip()
        obj.description = request.POST.get('description', '').strip()
        obj.is_default = request.POST.get('is_default') == 'on'
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        return _render_pipelines_list(request, hub_id)
    return django_render(request, 'leads/partials/panel_pipeline_edit.html', {'obj': obj})

@login_required
@require_POST
def pipeline_delete(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(Pipeline, pk=pk, hub_id=hub_id, is_deleted=False)
    obj.is_deleted = True
    obj.deleted_at = timezone.now()
    obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return _render_pipelines_list(request, hub_id)

@login_required
@require_POST
def pipeline_toggle_status(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(Pipeline, pk=pk, hub_id=hub_id, is_deleted=False)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active', 'updated_at'])
    return _render_pipelines_list(request, hub_id)

@login_required
@require_POST
def pipelines_bulk_action(request):
    hub_id = request.session.get('hub_id')
    ids = [i.strip() for i in request.POST.get('ids', '').split(',') if i.strip()]
    action = request.POST.get('action', '')
    qs = Pipeline.objects.filter(hub_id=hub_id, is_deleted=False, id__in=ids)
    if action == 'activate':
        qs.update(is_active=True)
    elif action == 'deactivate':
        qs.update(is_active=False)
    elif action == 'delete':
        qs.update(is_deleted=True, deleted_at=timezone.now())
    return _render_pipelines_list(request, hub_id)


# ======================================================================
# LossReason
# ======================================================================

LOSS_REASON_SORT_FIELDS = {
    'name': 'name',
    'is_active': 'is_active',
    'sort_order': 'sort_order',
    'created_at': 'created_at',
}

def _build_loss_reasons_context(hub_id, per_page=10):
    qs = LossReason.objects.filter(hub_id=hub_id, is_deleted=False).order_by('name')
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(1)
    return {
        'loss_reasons': page_obj,
        'page_obj': page_obj,
        'search_query': '',
        'sort_field': 'name',
        'sort_dir': 'asc',
        'current_view': 'table',
        'per_page': per_page,
    }

def _render_loss_reasons_list(request, hub_id, per_page=10):
    ctx = _build_loss_reasons_context(hub_id, per_page)
    return django_render(request, 'leads/partials/loss_reasons_list.html', ctx)

@login_required
@with_module_nav('leads', 'list')
@htmx_view('leads/pages/loss_reasons.html', 'leads/partials/loss_reasons_content.html')
def loss_reasons_list(request):
    hub_id = request.session.get('hub_id')
    search_query = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir', 'asc')
    page_number = request.GET.get('page', 1)
    current_view = request.GET.get('view', 'table')
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    qs = LossReason.objects.filter(hub_id=hub_id, is_deleted=False)

    if search_query:
        qs = qs.filter(Q(name__icontains=search_query))

    order_by = LOSS_REASON_SORT_FIELDS.get(sort_field, 'name')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    qs = qs.order_by(order_by)

    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        fields = ['name', 'is_active', 'sort_order']
        headers = ['Name', 'Is Active', 'Sort Order']
        if export_format == 'csv':
            return export_to_csv(qs, fields=fields, headers=headers, filename='loss_reasons.csv')
        return export_to_excel(qs, fields=fields, headers=headers, filename='loss_reasons.xlsx')

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'leads/partials/loss_reasons_list.html', {
            'loss_reasons': page_obj, 'page_obj': page_obj,
            'search_query': search_query, 'sort_field': sort_field,
            'sort_dir': sort_dir, 'current_view': current_view, 'per_page': per_page,
        })

    return {
        'loss_reasons': page_obj, 'page_obj': page_obj,
        'search_query': search_query, 'sort_field': sort_field,
        'sort_dir': sort_dir, 'current_view': current_view, 'per_page': per_page,
    }

@login_required
def loss_reason_add(request):
    hub_id = request.session.get('hub_id')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        sort_order = int(request.POST.get('sort_order', 0) or 0)
        obj = LossReason(hub_id=hub_id)
        obj.name = name
        obj.is_active = is_active
        obj.sort_order = sort_order
        obj.save()
        return _render_loss_reasons_list(request, hub_id)
    return django_render(request, 'leads/partials/panel_loss_reason_add.html', {})

@login_required
def loss_reason_edit(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(LossReason, pk=pk, hub_id=hub_id, is_deleted=False)
    if request.method == 'POST':
        obj.name = request.POST.get('name', '').strip()
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.sort_order = int(request.POST.get('sort_order', 0) or 0)
        obj.save()
        return _render_loss_reasons_list(request, hub_id)
    return django_render(request, 'leads/partials/panel_loss_reason_edit.html', {'obj': obj})

@login_required
@require_POST
def loss_reason_delete(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(LossReason, pk=pk, hub_id=hub_id, is_deleted=False)
    obj.is_deleted = True
    obj.deleted_at = timezone.now()
    obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return _render_loss_reasons_list(request, hub_id)

@login_required
@require_POST
def loss_reason_toggle_status(request, pk):
    hub_id = request.session.get('hub_id')
    obj = get_object_or_404(LossReason, pk=pk, hub_id=hub_id, is_deleted=False)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active', 'updated_at'])
    return _render_loss_reasons_list(request, hub_id)

@login_required
@require_POST
def loss_reasons_bulk_action(request):
    hub_id = request.session.get('hub_id')
    ids = [i.strip() for i in request.POST.get('ids', '').split(',') if i.strip()]
    action = request.POST.get('action', '')
    qs = LossReason.objects.filter(hub_id=hub_id, is_deleted=False, id__in=ids)
    if action == 'activate':
        qs.update(is_active=True)
    elif action == 'deactivate':
        qs.update(is_active=False)
    elif action == 'delete':
        qs.update(is_deleted=True, deleted_at=timezone.now())
    return _render_loss_reasons_list(request, hub_id)


# ======================================================================
# Settings
# ======================================================================

@login_required
@with_module_nav('leads', 'settings')
@htmx_view('leads/pages/settings.html', 'leads/partials/settings_content.html')
def settings_view(request):
    hub_id = request.session.get('hub_id')
    config, _ = LeadSettings.objects.get_or_create(hub_id=hub_id)
    if request.method == 'POST':
        config.default_pipeline = request.POST.get('default_pipeline', '').strip()
        config.auto_create_customer_on_win = request.POST.get('auto_create_customer_on_win') == 'on'
        config.default_source = request.POST.get('default_source', '').strip()
        config.save()
    return {'config': config}

