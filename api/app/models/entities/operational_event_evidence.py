from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalEventEvidence(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_event_evidence", null=True, on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="evidence", on_delete=fields.CASCADE)
    execution = fields.ForeignKeyField("models.OperationalEventExecution", related_name="evidence", null=True, on_delete=fields.CASCADE)
    attachment = fields.ForeignKeyField("models.Attachment", related_name="operational_event_evidence", null=True, on_delete=fields.SET_NULL)
    evidence_type = fields.CharField(max_length=40, default="attachment")
    description = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_event_evidence"
        indexes = (("company_id",), ("event_id",), ("execution_id",), ("attachment_id",), ("evidence_type",))

