from django.contrib import admin

from .models import Pipeline, PipelineStage, LossReason, Lead, LeadActivity, LeadSettings


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'is_active', 'created_at')
    list_filter = ('is_default', 'is_active')
    search_fields = ('name',)


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'pipeline', 'order', 'probability', 'color', 'is_won', 'is_lost')
    list_filter = ('pipeline', 'is_won', 'is_lost')
    ordering = ('pipeline', 'order')


@admin.register(LossReason)
class LossReasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    ordering = ('sort_order', 'name')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'value', 'pipeline', 'stage', 'status', 'priority', 'source', 'created_at')
    list_filter = ('status', 'priority', 'source', 'pipeline', 'stage')
    search_fields = ('name', 'email', 'phone', 'company')
    readonly_fields = ('won_date', 'lost_date', 'stage_changed_at')


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'activity_type', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('lead__name', 'description')


@admin.register(LeadSettings)
class LeadSettingsAdmin(admin.ModelAdmin):
    list_display = ('hub_id', 'default_source', 'auto_create_customer_on_win')
