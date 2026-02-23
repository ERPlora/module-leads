from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Pipeline (Kanban)
    path('pipeline/', views.pipeline, name='pipeline'),

    # Leads List
    path('list/', views.lead_list, name='list'),

    # Lead CRUD
    path('add/', views.lead_add, name='add'),
    path('<uuid:lead_id>/', views.lead_detail, name='detail'),
    path('<uuid:lead_id>/edit/', views.lead_edit, name='edit'),
    path('<uuid:lead_id>/delete/', views.lead_delete, name='delete'),

    # Lead Actions
    path('<uuid:lead_id>/move/', views.lead_move_stage, name='move_stage'),
    path('<uuid:lead_id>/convert/', views.lead_convert, name='convert'),
    path('<uuid:lead_id>/won/', views.lead_won, name='won'),
    path('<uuid:lead_id>/lost/', views.lead_lost, name='lost'),
    path('<uuid:lead_id>/activity/add/', views.lead_add_activity, name='add_activity'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # API
    path('api/pipeline-data/', views.pipeline_data_api, name='pipeline_data'),
]
