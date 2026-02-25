# Leads Module

Sales pipeline and lead management with visual Kanban board.

## Features

- Visual pipeline management with customizable stages and win probabilities
- Lead tracking with contact details, expected value, and close dates
- Multiple lead sources: manual, website, referral, campaign, social media, walk-in, phone, import
- Priority levels (low, medium, high, urgent) with color-coded indicators
- Automatic status transitions when leads move to won/lost stages
- Activity log for notes, calls, emails, meetings, and stage/status changes
- Convert leads to customers with one click (via customers module)
- Loss reason tracking for pipeline analytics
- Default pipeline auto-creation with standard sales stages
- Configurable settings: default pipeline, default source, auto-create customer on win

## Installation

This module is installed automatically via the ERPlora Marketplace.

**Dependencies**: Requires `customers` module.

## Configuration

Access settings via: **Menu > Leads > Settings**

Settings include:
- Default pipeline selection
- Auto-create customer on win toggle
- Default lead source

## Usage

Access via: **Menu > Leads**

### Views

| View | URL | Description |
|------|-----|-------------|
| Dashboard | `/m/leads/dashboard/` | Pipeline metrics and lead overview |
| Pipeline | `/m/leads/pipeline/` | Visual Kanban board with drag-and-drop stages |
| Leads | `/m/leads/list/` | List view of all leads with filtering |
| Settings | `/m/leads/settings/` | Module configuration, pipelines, stages, and loss reasons |

## Models

| Model | Description |
|-------|-------------|
| `Pipeline` | Sales pipeline with name, description, and default flag (one default per hub) |
| `PipelineStage` | Pipeline stage with order, win probability percentage, color, and auto-win/auto-lost flags |
| `LossReason` | Configurable reasons for lost leads |
| `Lead` | Lead record with contact info, value, pipeline/stage, source, priority, status, and customer link |
| `LeadActivity` | Activity log entry linked to a lead (notes, calls, emails, meetings, stage/status changes) |
| `LeadSettings` | Singleton per-hub settings for default pipeline, source, and auto-create behavior |

## Permissions

| Permission | Description |
|------------|-------------|
| `leads.view_lead` | View leads |
| `leads.add_lead` | Create new leads |
| `leads.change_lead` | Edit existing leads |
| `leads.delete_lead` | Delete leads |
| `leads.view_pipeline` | View pipelines and stages |
| `leads.manage_pipeline` | Create and edit pipelines and stages |
| `leads.convert_lead` | Convert a lead to a customer |
| `leads.manage_settings` | Manage module settings |

## Integration with Other Modules

- **customers**: Leads can be linked to existing customers. Won leads can be automatically converted to customer records via the `convert_to_customer()` method.

## License

MIT

## Author

ERPlora Team - support@erplora.com
