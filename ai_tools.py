"""AI tools for the Leads (CRM) module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListLeads(AssistantTool):
    name = "list_leads"
    description = "List leads with optional filters. Returns name, company, value, stage, status."
    module_id = "leads"
    required_permission = "leads.view_lead"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: open, won, lost"},
            "pipeline_id": {"type": "string", "description": "Filter by pipeline ID"},
            "search": {"type": "string", "description": "Search by name, email, or company"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from leads.models import Lead
        from django.db.models import Q
        qs = Lead.objects.select_related('stage', 'pipeline').all()
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        if args.get('pipeline_id'):
            qs = qs.filter(pipeline_id=args['pipeline_id'])
        if args.get('search'):
            s = args['search']
            qs = qs.filter(Q(name__icontains=s) | Q(email__icontains=s) | Q(company__icontains=s))
        limit = args.get('limit', 20)
        return {
            "leads": [
                {
                    "id": str(l.id),
                    "name": l.name,
                    "email": l.email,
                    "company": l.company,
                    "value": str(l.value) if l.value else None,
                    "stage": l.stage.name if l.stage else None,
                    "pipeline": l.pipeline.name if l.pipeline else None,
                    "status": l.status,
                    "priority": l.priority,
                    "source": l.source,
                }
                for l in qs.order_by('-created_at')[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class CreateLead(AssistantTool):
    name = "create_lead"
    description = "Create a new lead in the CRM pipeline."
    module_id = "leads"
    required_permission = "leads.change_lead"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Contact name"},
            "email": {"type": "string", "description": "Email"},
            "phone": {"type": "string", "description": "Phone"},
            "company": {"type": "string", "description": "Company name"},
            "value": {"type": "string", "description": "Expected deal value"},
            "source": {"type": "string", "description": "Lead source"},
            "priority": {"type": "string", "description": "Priority: low, medium, high"},
            "pipeline_id": {"type": "string", "description": "Pipeline ID"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from leads.models import Lead, Pipeline, PipelineStage
        pipeline_id = args.get('pipeline_id')
        if not pipeline_id:
            pipeline = Pipeline.objects.first()
        else:
            pipeline = Pipeline.objects.get(id=pipeline_id)
        first_stage = PipelineStage.objects.filter(pipeline=pipeline).order_by('order').first() if pipeline else None
        lead = Lead.objects.create(
            name=args['name'],
            email=args.get('email', ''),
            phone=args.get('phone', ''),
            company=args.get('company', ''),
            value=Decimal(args['value']) if args.get('value') else None,
            source=args.get('source', ''),
            priority=args.get('priority', 'medium'),
            pipeline=pipeline,
            stage=first_stage,
            status='open',
        )
        return {"id": str(lead.id), "name": lead.name, "stage": first_stage.name if first_stage else None, "created": True}


@register_tool
class MoveLeadStage(AssistantTool):
    name = "move_lead_stage"
    description = "Move a lead to a different pipeline stage."
    module_id = "leads"
    required_permission = "leads.change_lead"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID"},
            "stage_id": {"type": "string", "description": "Target stage ID"},
        },
        "required": ["lead_id", "stage_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from leads.models import Lead, PipelineStage
        lead = Lead.objects.get(id=args['lead_id'])
        stage = PipelineStage.objects.get(id=args['stage_id'])
        lead.stage = stage
        if stage.is_won:
            lead.status = 'won'
        elif stage.is_lost:
            lead.status = 'lost'
        lead.save()
        return {"id": str(lead.id), "name": lead.name, "new_stage": stage.name, "status": lead.status}


@register_tool
class GetPipelineOverview(AssistantTool):
    name = "get_pipeline_overview"
    description = "Get an overview of leads by pipeline stage with counts and values."
    module_id = "leads"
    required_permission = "leads.view_lead"
    parameters = {
        "type": "object",
        "properties": {
            "pipeline_id": {"type": "string", "description": "Pipeline ID (uses default if omitted)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from django.db.models import Count, Sum
        from leads.models import Pipeline, PipelineStage, Lead
        if args.get('pipeline_id'):
            pipeline = Pipeline.objects.get(id=args['pipeline_id'])
        else:
            pipeline = Pipeline.objects.first()
        if not pipeline:
            return {"error": "No pipeline found"}
        stages = PipelineStage.objects.filter(pipeline=pipeline).order_by('order')
        result = []
        for stage in stages:
            leads = Lead.objects.filter(stage=stage, status='open')
            stats = leads.aggregate(count=Count('id'), total_value=Sum('value'))
            result.append({
                "stage": stage.name,
                "probability": stage.probability,
                "lead_count": stats['count'] or 0,
                "total_value": str(stats['total_value'] or 0),
            })
        return {"pipeline": pipeline.name, "stages": result}
