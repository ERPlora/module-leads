from django.utils.translation import gettext_lazy as _

MODULE_ID = 'leads'
MODULE_NAME = _('Leads')
MODULE_VERSION = '1.0.0'
MODULE_ICON = 'funnel-outline'
MODULE_DESCRIPTION = _('Sales pipeline and lead management with visual Kanban board')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = 'sales'

MENU = {
    'label': _('Leads'),
    'icon': 'funnel-outline',
    'order': 15,
}

NAVIGATION = [
    {'label': _('Dashboard'), 'icon': 'speedometer-outline', 'id': 'dashboard'},
    {'label': _('Pipeline'), 'icon': 'git-branch-outline', 'id': 'pipeline'},
    {'label': _('Leads'), 'icon': 'people-outline', 'id': 'list'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

DEPENDENCIES = ['customers']

PERMISSIONS = [
    'leads.view_lead',
    'leads.add_lead',
    'leads.change_lead',
    'leads.delete_lead',
    'leads.view_pipeline',
    'leads.manage_pipeline',
    'leads.convert_lead',
    'leads.manage_settings',
]
