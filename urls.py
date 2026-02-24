from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Pipeline
    path('pipelines/', views.pipelines_list, name='pipelines_list'),
    path('pipelines/add/', views.pipeline_add, name='pipeline_add'),
    path('pipelines/<uuid:pk>/edit/', views.pipeline_edit, name='pipeline_edit'),
    path('pipelines/<uuid:pk>/delete/', views.pipeline_delete, name='pipeline_delete'),
    path('pipelines/<uuid:pk>/toggle/', views.pipeline_toggle_status, name='pipeline_toggle_status'),
    path('pipelines/bulk/', views.pipelines_bulk_action, name='pipelines_bulk_action'),

    # LossReason
    path('loss_reasons/', views.loss_reasons_list, name='loss_reasons_list'),
    path('loss_reasons/add/', views.loss_reason_add, name='loss_reason_add'),
    path('loss_reasons/<uuid:pk>/edit/', views.loss_reason_edit, name='loss_reason_edit'),
    path('loss_reasons/<uuid:pk>/delete/', views.loss_reason_delete, name='loss_reason_delete'),
    path('loss_reasons/<uuid:pk>/toggle/', views.loss_reason_toggle_status, name='loss_reason_toggle_status'),
    path('loss_reasons/bulk/', views.loss_reasons_bulk_action, name='loss_reasons_bulk_action'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
