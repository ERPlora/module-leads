"""
AI context for the Leads module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Leads

### Models

**Pipeline** — A sales pipeline (e.g., "Sales Pipeline", "Partnership Deals").
- `name`, `description`
- `is_default` (only one per hub), `is_active`
- Properties: `lead_count` (open leads), `total_value` (sum of open lead values)

**PipelineStage** — A stage within a pipeline (e.g., New, Contacted, Proposal, Won).
- `pipeline` FK → Pipeline (related_name='stages')
- `name`, `order` (sort order), `probability` (0-100 win %)
- `color`: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info'
- `is_won`: Moving a lead here auto-marks it as Won
- `is_lost`: Moving a lead here auto-marks it as Lost

**LossReason** — Predefined reasons for losing a lead.
- `name`, `is_active`, `sort_order`

**Lead** — A sales opportunity.
- `name`, `email`, `phone`, `company`
- `value` (Decimal): Expected deal value
- `expected_close_date` (DateField, optional)
- `pipeline` FK → Pipeline, `stage` FK → PipelineStage
- `assigned_to` (UUIDField, optional): UUID of the assigned user
- `customer` FK → customers.Customer (optional; set on conversion)
- `source`: 'manual' | 'website' | 'referral' | 'campaign' | 'social' | 'import' | 'walk_in' | 'phone' | 'other'
- `priority`: 'low' | 'medium' | 'high' | 'urgent'
- `notes`
- `status`: 'open' | 'won' | 'lost'
- `won_date`, `lost_date`, `loss_reason` FK → LossReason
- `stage_changed_at`: Timestamp of last stage change
- Methods: `mark_won()`, `mark_lost(loss_reason)`, `move_to_stage(new_stage)`, `convert_to_customer()`

**LeadActivity** — Audit trail of actions on a lead.
- `lead` FK → Lead (related_name='activities')
- `activity_type`: 'note' | 'call' | 'email' | 'meeting' | 'stage_change' | 'status_change'
- `description`, `metadata` (JSONField)

**LeadSettings** — Per-hub settings (singleton).
- `default_pipeline` FK → Pipeline
- `auto_create_customer_on_win` (bool)
- `default_source`
- Use `LeadSettings.get_settings(hub_id)`

### Key Flows

1. **Create lead**: Create Lead in a pipeline's stage (status='open') → LeadActivity auto-created on status/stage changes
2. **Move through pipeline**: `lead.move_to_stage(new_stage)` → updates stage_changed_at, creates LeadActivity; if stage.is_won → auto calls mark_won(); if stage.is_lost → auto calls mark_lost()
3. **Win lead**: `lead.mark_won()` → status='won', won_date=now; if auto_create_customer_on_win → `convert_to_customer()` runs automatically
4. **Lose lead**: `lead.mark_lost(loss_reason)` → status='lost', lost_date=now
5. **Convert to customer**: `lead.convert_to_customer()` → creates customers.Customer from lead's name/email/phone → links lead.customer FK

### Default Pipeline Stages
If no pipeline exists, `ensure_default_pipeline(hub_id)` creates one with stages: New (10%) → Contacted (20%) → Qualified (40%) → Proposal (60%) → Negotiation (80%) → Won (100%, is_won=True) → Lost (0%, is_lost=True)

### Relationships
- `Lead.customer` → customers.Customer
- `Lead.pipeline` → Pipeline, `Lead.stage` → PipelineStage
- `Lead.loss_reason` → LossReason
"""
