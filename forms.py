from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Pipeline, LossReason, LeadSettings

class PipelineForm(forms.ModelForm):
    class Meta:
        model = Pipeline
        fields = ['name', 'description', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-sm w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-sm w-full', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }

class LossReasonForm(forms.ModelForm):
    class Meta:
        model = LossReason
        fields = ['name', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-sm w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'sort_order': forms.TextInput(attrs={'class': 'input input-sm w-full', 'type': 'number'}),
        }

class LeadSettingsForm(forms.ModelForm):
    class Meta:
        model = LeadSettings
        fields = ['default_pipeline', 'auto_create_customer_on_win', 'default_source']
        widgets = {
            'default_pipeline': forms.Select(attrs={'class': 'select select-sm w-full'}),
            'auto_create_customer_on_win': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'default_source': forms.Select(attrs={'class': 'select select-sm w-full'}),
        }

