# Leads

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `leads` |
| **Version** | `1.0.0` |
| **Icon** | `funnel-outline` |
| **Dependencies** | `customers` |

## Dependencies

This module requires the following modules to be installed:

- `customers`

## Models

### `Pipeline`

Pipeline(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, name, description, is_default, is_active)

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `is_default` | BooleanField |  |
| `is_active` | BooleanField |  |

**Properties:**

- `lead_count`
- `total_value`

### `PipelineStage`

PipelineStage(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, pipeline, name, order, probability, color, is_won, is_lost)

| Field | Type | Details |
|-------|------|---------|
| `pipeline` | ForeignKey | → `leads.Pipeline`, on_delete=CASCADE |
| `name` | CharField | max_length=100 |
| `order` | PositiveIntegerField |  |
| `probability` | PositiveIntegerField |  |
| `color` | CharField | max_length=20, choices: primary, secondary, success, warning, danger, info |
| `is_won` | BooleanField |  |
| `is_lost` | BooleanField |  |

**Properties:**

- `lead_count`
- `total_value`

### `LossReason`

LossReason(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, name, is_active, sort_order)

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `is_active` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |

### `Lead`

Lead(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, name, email, phone, company, value, expected_close_date, pipeline, stage, assigned_to, customer, source, priority, notes, status, won_date, lost_date, loss_reason, stage_changed_at)

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=255 |
| `email` | EmailField | max_length=254, optional |
| `phone` | CharField | max_length=20, optional |
| `company` | CharField | max_length=255, optional |
| `value` | DecimalField |  |
| `expected_close_date` | DateField | optional |
| `pipeline` | ForeignKey | → `leads.Pipeline`, on_delete=CASCADE |
| `stage` | ForeignKey | → `leads.PipelineStage`, on_delete=CASCADE |
| `assigned_to` | UUIDField | max_length=32, optional |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `source` | CharField | max_length=20, choices: manual, website, referral, campaign, social, import, ... |
| `priority` | CharField | max_length=10, choices: low, medium, high, urgent |
| `notes` | TextField | optional |
| `status` | CharField | max_length=10, choices: open, won, lost |
| `won_date` | DateTimeField | optional |
| `lost_date` | DateTimeField | optional |
| `loss_reason` | ForeignKey | → `leads.LossReason`, on_delete=SET_NULL, optional |
| `stage_changed_at` | DateTimeField | optional |

**Methods:**

- `mark_won()` — Mark this lead as won.
- `mark_lost()` — Mark this lead as lost.
- `move_to_stage()` — Move lead to a new pipeline stage.
- `convert_to_customer()` — Create a Customer from this lead's data.
Returns the created Customer or None if customers module not available.

**Properties:**

- `initials`
- `days_in_stage`
- `days_open`
- `priority_color`
- `status_color`

### `LeadActivity`

LeadActivity(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, lead, activity_type, description, metadata)

| Field | Type | Details |
|-------|------|---------|
| `lead` | ForeignKey | → `leads.Lead`, on_delete=CASCADE |
| `activity_type` | CharField | max_length=20, choices: note, call, email, meeting, stage_change, status_change |
| `description` | TextField |  |
| `metadata` | JSONField | optional |

**Properties:**

- `icon`
- `color`

### `LeadSettings`

LeadSettings(id, hub_id, created_at, updated_at, created_by, updated_by, is_deleted, deleted_at, default_pipeline, auto_create_customer_on_win, default_source)

| Field | Type | Details |
|-------|------|---------|
| `default_pipeline` | ForeignKey | → `leads.Pipeline`, on_delete=SET_NULL, optional |
| `auto_create_customer_on_win` | BooleanField |  |
| `default_source` | CharField | max_length=20, choices: manual, website, referral, campaign, social, import, ... |

**Methods:**

- `get_settings()` — Get or create the singleton settings for this hub.

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `PipelineStage` | `pipeline` | `leads.Pipeline` | CASCADE | No |
| `Lead` | `pipeline` | `leads.Pipeline` | CASCADE | No |
| `Lead` | `stage` | `leads.PipelineStage` | CASCADE | No |
| `Lead` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `Lead` | `loss_reason` | `leads.LossReason` | SET_NULL | Yes |
| `LeadActivity` | `lead` | `leads.Lead` | CASCADE | No |
| `LeadSettings` | `default_pipeline` | `leads.Pipeline` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/leads/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `dashboard` | GET |
| `pipeline/` | `pipeline` | GET |
| `list/` | `list` | GET |
| `pipelines/` | `pipelines_list` | GET |
| `pipelines/add/` | `pipeline_add` | GET/POST |
| `pipelines/<uuid:pk>/edit/` | `pipeline_edit` | GET |
| `pipelines/<uuid:pk>/delete/` | `pipeline_delete` | GET/POST |
| `pipelines/<uuid:pk>/toggle/` | `pipeline_toggle_status` | GET |
| `pipelines/bulk/` | `pipelines_bulk_action` | GET/POST |
| `loss_reasons/` | `loss_reasons_list` | GET |
| `loss_reasons/add/` | `loss_reason_add` | GET/POST |
| `loss_reasons/<uuid:pk>/edit/` | `loss_reason_edit` | GET |
| `loss_reasons/<uuid:pk>/delete/` | `loss_reason_delete` | GET/POST |
| `loss_reasons/<uuid:pk>/toggle/` | `loss_reason_toggle_status` | GET |
| `loss_reasons/bulk/` | `loss_reasons_bulk_action` | GET/POST |
| `settings/` | `settings` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `leads.view_lead` | View Lead |
| `leads.add_lead` | Add Lead |
| `leads.change_lead` | Change Lead |
| `leads.delete_lead` | Delete Lead |
| `leads.view_pipeline` | View Pipeline |
| `leads.manage_pipeline` | Manage Pipeline |
| `leads.convert_lead` | Convert Lead |
| `leads.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_lead`, `change_lead`, `convert_lead`, `manage_pipeline`, `view_lead`, `view_pipeline`
- **employee**: `add_lead`, `view_lead`, `view_pipeline`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `speedometer-outline` | `dashboard` | No |
| Pipeline | `git-branch-outline` | `pipeline` | No |
| Leads | `people-outline` | `list` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_leads`

List leads with optional filters. Returns name, company, value, stage, status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: open, won, lost |
| `pipeline_id` | string | No | Filter by pipeline ID |
| `search` | string | No | Search by name, email, or company |
| `limit` | integer | No | Max results (default 20) |

### `create_lead`

Create a new lead in the CRM pipeline.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Contact name |
| `email` | string | No | Email |
| `phone` | string | No | Phone |
| `company` | string | No | Company name |
| `value` | string | No | Expected deal value |
| `source` | string | No | Lead source |
| `priority` | string | No | Priority: low, medium, high |
| `pipeline_id` | string | No | Pipeline ID |

### `move_lead_stage`

Move a lead to a different pipeline stage.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string | Yes | Lead ID |
| `stage_id` | string | Yes | Target stage ID |

### `get_pipeline_overview`

Get an overview of leads by pipeline stage with counts and values.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline_id` | string | No | Pipeline ID (uses default if omitted) |

## File Structure

```
README.md
__init__.py
admin.py
ai_tools.py
apps.py
forms.py
locale/
  en/
    LC_MESSAGES/
      django.po
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
static/
  leads/
    css/
      kanban.css
    js/
templates/
  leads/
    pages/
      dashboard.html
      index.html
      lead_add.html
      lead_edit.html
      list.html
      loss_reason_add.html
      loss_reason_edit.html
      loss_reasons.html
      pipeline.html
      pipeline_add.html
      pipeline_edit.html
      pipelines.html
      settings.html
    partials/
      dashboard_content.html
      lead_add_content.html
      lead_detail.html
      lead_edit_content.html
      leads_content.html
      leads_list.html
      loss_reason_add_content.html
      loss_reason_edit_content.html
      loss_reasons_content.html
      loss_reasons_list.html
      panel_lead_add.html
      panel_lead_edit.html
      panel_loss_reason_add.html
      panel_loss_reason_edit.html
      panel_pipeline_add.html
      panel_pipeline_edit.html
      pipeline_add_content.html
      pipeline_content.html
      pipeline_edit_content.html
      pipelines_content.html
      pipelines_list.html
      settings_content.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_views.py
urls.py
views.py
```
