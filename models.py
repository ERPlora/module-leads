from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import HubBaseModel


# ============================================================================
# Choices
# ============================================================================

SOURCE_CHOICES = [
    ('manual', _('Manual')),
    ('website', _('Website')),
    ('referral', _('Referral')),
    ('campaign', _('Campaign')),
    ('social', _('Social Media')),
    ('import', _('Import')),
    ('walk_in', _('Walk-in')),
    ('phone', _('Phone Call')),
    ('other', _('Other')),
]

PRIORITY_CHOICES = [
    ('low', _('Low')),
    ('medium', _('Medium')),
    ('high', _('High')),
    ('urgent', _('Urgent')),
]

STATUS_CHOICES = [
    ('open', _('Open')),
    ('won', _('Won')),
    ('lost', _('Lost')),
]

ACTIVITY_TYPE_CHOICES = [
    ('note', _('Note')),
    ('call', _('Call')),
    ('email', _('Email')),
    ('meeting', _('Meeting')),
    ('stage_change', _('Stage Change')),
    ('status_change', _('Status Change')),
]

STAGE_COLORS = [
    ('primary', _('Primary')),
    ('secondary', _('Secondary')),
    ('success', _('Success')),
    ('warning', _('Warning')),
    ('danger', _('Danger')),
    ('info', _('Info')),
]


# ============================================================================
# Pipeline
# ============================================================================

class Pipeline(HubBaseModel):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_default = models.BooleanField(default=False, verbose_name=_('Default Pipeline'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_pipeline'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default pipeline per hub
        if self.is_default and self.hub_id:
            Pipeline.objects.filter(
                hub_id=self.hub_id, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def lead_count(self):
        return self.leads.filter(is_deleted=False, status='open').count()

    @property
    def total_value(self):
        result = self.leads.filter(
            is_deleted=False, status='open'
        ).aggregate(total=models.Sum('value'))
        return result['total'] or Decimal('0.00')


# ============================================================================
# Pipeline Stage
# ============================================================================

class PipelineStage(HubBaseModel):
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE,
        related_name='stages', verbose_name=_('Pipeline'),
    )
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    probability = models.PositiveIntegerField(
        default=0, verbose_name=_('Probability (%)'),
        help_text=_('Win probability percentage (0-100)'),
    )
    color = models.CharField(
        max_length=20, default='primary',
        choices=STAGE_COLORS, verbose_name=_('Color'),
    )
    is_won = models.BooleanField(
        default=False, verbose_name=_('Won Stage'),
        help_text=_('Leads moved here are automatically marked as won'),
    )
    is_lost = models.BooleanField(
        default=False, verbose_name=_('Lost Stage'),
        help_text=_('Leads moved here are automatically marked as lost'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_pipelinestage'
        ordering = ['order']

    def __str__(self):
        return f'{self.pipeline.name} - {self.name}'

    @property
    def lead_count(self):
        return self.leads.filter(is_deleted=False, status='open').count()

    @property
    def total_value(self):
        result = self.leads.filter(
            is_deleted=False, status='open'
        ).aggregate(total=models.Sum('value'))
        return result['total'] or Decimal('0.00')


# ============================================================================
# Loss Reason
# ============================================================================

class LossReason(HubBaseModel):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_lossreason'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# Lead
# ============================================================================

class Lead(HubBaseModel):
    # Basic info
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    company = models.CharField(max_length=255, blank=True, verbose_name=_('Company'))

    # Value
    value = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Expected Value'),
    )
    expected_close_date = models.DateField(
        null=True, blank=True, verbose_name=_('Expected Close Date'),
    )

    # Pipeline
    pipeline = models.ForeignKey(
        Pipeline, on_delete=models.CASCADE,
        related_name='leads', verbose_name=_('Pipeline'),
    )
    stage = models.ForeignKey(
        PipelineStage, on_delete=models.CASCADE,
        related_name='leads', verbose_name=_('Stage'),
    )

    # Assignment
    assigned_to = models.UUIDField(
        null=True, blank=True, verbose_name=_('Assigned To'),
        help_text=_('UUID of the assigned user'),
    )

    # Customer link
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leads',
        verbose_name=_('Customer'),
    )

    # Classification
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES,
        default='manual', verbose_name=_('Source'),
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES,
        default='medium', verbose_name=_('Priority'),
    )

    # Notes
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    # Status tracking
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default='open', verbose_name=_('Status'),
    )
    won_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Won Date'),
    )
    lost_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Lost Date'),
    )
    loss_reason = models.ForeignKey(
        LossReason, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leads',
        verbose_name=_('Loss Reason'),
    )

    # Stage tracking
    stage_changed_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Stage Changed At'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_lead'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'status']),
            models.Index(fields=['hub_id', 'pipeline', 'stage']),
            models.Index(fields=['hub_id', 'assigned_to']),
            models.Index(fields=['hub_id', 'source']),
            models.Index(fields=['hub_id', 'priority']),
        ]

    def __str__(self):
        return self.name

    @property
    def initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.name[:2].upper() if self.name else '??'

    @property
    def days_in_stage(self):
        if self.stage_changed_at:
            delta = timezone.now() - self.stage_changed_at
            return delta.days
        return 0

    @property
    def days_open(self):
        if self.status == 'open':
            delta = timezone.now() - self.created_at
            return delta.days
        elif self.status == 'won' and self.won_date:
            delta = self.won_date - self.created_at
            return delta.days
        elif self.status == 'lost' and self.lost_date:
            delta = self.lost_date - self.created_at
            return delta.days
        return 0

    @property
    def priority_color(self):
        colors = {
            'low': 'secondary',
            'medium': 'primary',
            'high': 'warning',
            'urgent': 'danger',
        }
        return colors.get(self.priority, 'primary')

    @property
    def status_color(self):
        colors = {
            'open': 'primary',
            'won': 'success',
            'lost': 'danger',
        }
        return colors.get(self.status, 'primary')

    def mark_won(self):
        """Mark this lead as won."""
        self.status = 'won'
        self.won_date = timezone.now()
        self.save(update_fields=['status', 'won_date', 'updated_at'])
        LeadActivity.objects.create(
            hub_id=self.hub_id,
            lead=self,
            activity_type='status_change',
            description=str(_('Lead marked as won')),
            metadata={'new_status': 'won'},
        )

    def mark_lost(self, loss_reason=None):
        """Mark this lead as lost."""
        self.status = 'lost'
        self.lost_date = timezone.now()
        self.loss_reason = loss_reason
        update_fields = ['status', 'lost_date', 'loss_reason', 'updated_at']
        self.save(update_fields=update_fields)
        metadata = {'new_status': 'lost'}
        if loss_reason:
            metadata['loss_reason'] = str(loss_reason.name)
        LeadActivity.objects.create(
            hub_id=self.hub_id,
            lead=self,
            activity_type='status_change',
            description=str(_('Lead marked as lost')),
            metadata=metadata,
        )

    def move_to_stage(self, new_stage):
        """Move lead to a new pipeline stage."""
        old_stage = self.stage
        self.stage = new_stage
        self.stage_changed_at = timezone.now()
        self.save(update_fields=['stage', 'stage_changed_at', 'updated_at'])
        LeadActivity.objects.create(
            hub_id=self.hub_id,
            lead=self,
            activity_type='stage_change',
            description=str(_('Stage changed from %(old)s to %(new)s') % {
                'old': old_stage.name, 'new': new_stage.name,
            }),
            metadata={
                'old_stage': str(old_stage.id),
                'old_stage_name': old_stage.name,
                'new_stage': str(new_stage.id),
                'new_stage_name': new_stage.name,
            },
        )
        # Auto-win or auto-lose based on stage flags
        if new_stage.is_won:
            self.mark_won()
        elif new_stage.is_lost:
            self.mark_lost()

    def convert_to_customer(self):
        """
        Create a Customer from this lead's data.
        Returns the created Customer or None if customers module not available.
        """
        try:
            from customers.models import Customer
            customer = Customer.objects.create(
                hub_id=self.hub_id,
                name=self.company or self.name,
                email=self.email,
                phone=self.phone,
            )
            self.customer = customer
            self.save(update_fields=['customer', 'updated_at'])
            LeadActivity.objects.create(
                hub_id=self.hub_id,
                lead=self,
                activity_type='note',
                description=str(_('Lead converted to customer: %(name)s') % {
                    'name': customer.name,
                }),
                metadata={'customer_id': str(customer.id)},
            )
            return customer
        except (ImportError, Exception):
            return None


# ============================================================================
# Lead Activity
# ============================================================================

class LeadActivity(HubBaseModel):
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='activities', verbose_name=_('Lead'),
    )
    activity_type = models.CharField(
        max_length=20, choices=ACTIVITY_TYPE_CHOICES,
        verbose_name=_('Activity Type'),
    )
    description = models.TextField(verbose_name=_('Description'))
    metadata = models.JSONField(
        default=dict, blank=True, verbose_name=_('Metadata'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_leadactivity'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_activity_type_display()} - {self.lead.name}'

    @property
    def icon(self):
        icons = {
            'note': 'document-text-outline',
            'call': 'call-outline',
            'email': 'mail-outline',
            'meeting': 'calendar-outline',
            'stage_change': 'git-branch-outline',
            'status_change': 'flag-outline',
        }
        return icons.get(self.activity_type, 'ellipsis-horizontal-outline')

    @property
    def color(self):
        colors = {
            'note': 'primary',
            'call': 'success',
            'email': 'info',
            'meeting': 'warning',
            'stage_change': 'secondary',
            'status_change': 'danger',
        }
        return colors.get(self.activity_type, 'primary')


# ============================================================================
# Lead Settings (Singleton per Hub)
# ============================================================================

class LeadSettings(HubBaseModel):
    default_pipeline = models.ForeignKey(
        Pipeline, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
        verbose_name=_('Default Pipeline'),
    )
    auto_create_customer_on_win = models.BooleanField(
        default=False, verbose_name=_('Auto-create Customer on Win'),
        help_text=_('Automatically create a customer record when a lead is won'),
    )
    default_source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES,
        default='manual', verbose_name=_('Default Source'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'leads_leadsettings'

    def __str__(self):
        return str(_('Lead Settings'))

    @classmethod
    def get_settings(cls, hub_id):
        """Get or create the singleton settings for this hub."""
        settings, _ = cls.objects.get_or_create(hub_id=hub_id)
        return settings


# ============================================================================
# Helper: Ensure default pipeline
# ============================================================================

def ensure_default_pipeline(hub_id):
    """
    Create a default pipeline with standard stages if none exists.
    Returns the default pipeline.
    """
    pipeline = Pipeline.objects.filter(hub_id=hub_id, is_deleted=False).first()
    if pipeline:
        return pipeline

    pipeline = Pipeline.objects.create(
        hub_id=hub_id,
        name=str(_('Sales Pipeline')),
        description=str(_('Default sales pipeline')),
        is_default=True,
    )

    default_stages = [
        {'name': str(_('New')), 'order': 10, 'probability': 10, 'color': 'info'},
        {'name': str(_('Contacted')), 'order': 20, 'probability': 20, 'color': 'primary'},
        {'name': str(_('Qualified')), 'order': 30, 'probability': 40, 'color': 'primary'},
        {'name': str(_('Proposal')), 'order': 40, 'probability': 60, 'color': 'warning'},
        {'name': str(_('Negotiation')), 'order': 50, 'probability': 80, 'color': 'warning'},
        {'name': str(_('Won')), 'order': 60, 'probability': 100, 'color': 'success', 'is_won': True},
        {'name': str(_('Lost')), 'order': 70, 'probability': 0, 'color': 'danger', 'is_lost': True},
    ]

    for stage_data in default_stages:
        PipelineStage.objects.create(
            hub_id=hub_id,
            pipeline=pipeline,
            **stage_data,
        )

    # Set default in settings
    settings = LeadSettings.get_settings(hub_id)
    settings.default_pipeline = pipeline
    settings.save(update_fields=['default_pipeline', 'updated_at'])

    return pipeline
