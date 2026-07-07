from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalEventExecution(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_event_executions", null=True, on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="executions", on_delete=fields.CASCADE)
    executed_by_user = fields.ForeignKeyField("models.User", related_name="operational_event_executions", null=True, on_delete=fields.SET_NULL)
    executed_at = fields.DatetimeField(null=True)
    result = fields.CharField(max_length=60, default="pending")
    comments = fields.TextField(null=True)
    requires_follow_up = fields.BooleanField(default=False)
    related_incident = fields.ForeignKeyField("models.Incident", related_name="operational_event_executions", null=True, on_delete=fields.SET_NULL)
    related_ticket = fields.ForeignKeyField("models.SupportTicket", related_name="operational_event_executions", null=True, on_delete=fields.SET_NULL)
    validation_status = fields.CharField(max_length=40, default="not_validated")
    validated_by_user = fields.ForeignKeyField("models.User", related_name="validated_operational_event_executions", null=True, on_delete=fields.SET_NULL)
    validated_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_event_executions"
        indexes = (("company_id",), ("event_id",), ("executed_by_user_id",), ("result",), ("validation_status",), ("executed_at",))

