from django.contrib import admin

from .models import Pipeline, PipelineStage, LossReason, Lead, LeadActivity

@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['pipeline', 'name', 'order', 'probability', 'color', 'created_at']
    search_fields = ['name', 'color']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LossReason)
class LossReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'sort_order', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'company', 'value', 'created_at']
    search_fields = ['name', 'email', 'phone', 'company']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'created_at']
    search_fields = ['activity_type', 'description']
    readonly_fields = ['created_at', 'updated_at']

