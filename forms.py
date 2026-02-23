from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Lead, Pipeline, PipelineStage, LossReason, LeadSettings,
    SOURCE_CHOICES, PRIORITY_CHOICES, STAGE_COLORS,
)


class LeadForm(forms.ModelForm):
    """Form for creating and editing leads."""

    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'phone', 'company', 'value',
            'expected_close_date', 'pipeline', 'stage',
            'source', 'priority', 'notes', 'customer',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('Lead name'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('email@example.com'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('+34 600 000 000'),
            }),
            'company': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('Company name'),
            }),
            'value': forms.NumberInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01',
            }),
            'expected_close_date': forms.DateInput(attrs={
                'class': 'input input-sm w-full',
                'type': 'date',
            }),
            'pipeline': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'stage': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'source': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'priority': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-sm w-full',
                'rows': '3',
                'placeholder': _('Additional notes...'),
            }),
            'customer': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
        }


class PipelineForm(forms.ModelForm):
    """Form for creating and editing pipelines."""

    class Meta:
        model = Pipeline
        fields = ['name', 'description', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('Pipeline name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-sm w-full',
                'rows': '2',
                'placeholder': _('Pipeline description'),
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class PipelineStageForm(forms.ModelForm):
    """Form for creating and editing pipeline stages."""

    class Meta:
        model = PipelineStage
        fields = ['name', 'order', 'probability', 'color', 'is_won', 'is_lost']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('Stage name'),
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input input-sm w-full',
                'min': '0',
            }),
            'probability': forms.NumberInput(attrs={
                'class': 'input input-sm w-full',
                'min': '0',
                'max': '100',
            }),
            'color': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'is_won': forms.CheckboxInput(attrs={
                'class': 'toggle color-success',
            }),
            'is_lost': forms.CheckboxInput(attrs={
                'class': 'toggle color-danger',
            }),
        }


class LossReasonForm(forms.ModelForm):
    """Form for creating and editing loss reasons."""

    class Meta:
        model = LossReason
        fields = ['name', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-sm w-full',
                'placeholder': _('Reason name'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input input-sm w-full',
                'min': '0',
            }),
        }


class LeadSettingsForm(forms.ModelForm):
    """Form for lead module settings."""

    class Meta:
        model = LeadSettings
        fields = ['default_pipeline', 'auto_create_customer_on_win', 'default_source']
        widgets = {
            'default_pipeline': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
            'auto_create_customer_on_win': forms.CheckboxInput(attrs={
                'class': 'toggle color-success',
            }),
            'default_source': forms.Select(attrs={
                'class': 'select select-sm w-full',
            }),
        }


class LeadActivityForm(forms.Form):
    """Form for adding activities to a lead."""

    activity_type = forms.ChoiceField(
        choices=[
            ('note', _('Note')),
            ('call', _('Call')),
            ('email', _('Email')),
            ('meeting', _('Meeting')),
        ],
        widget=forms.Select(attrs={
            'class': 'select select-sm w-full',
        }),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-sm w-full',
            'rows': '3',
            'placeholder': _('Describe the activity...'),
        }),
    )


class LeadLostForm(forms.Form):
    """Form for marking a lead as lost with a reason."""

    loss_reason = forms.ModelChoiceField(
        queryset=LossReason.objects.none(),
        required=False,
        empty_label=_('Select a reason...'),
        widget=forms.Select(attrs={
            'class': 'select select-sm w-full',
        }),
    )

    def __init__(self, *args, hub_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hub_id:
            self.fields['loss_reason'].queryset = LossReason.objects.filter(
                hub_id=hub_id, is_deleted=False, is_active=True,
            )
