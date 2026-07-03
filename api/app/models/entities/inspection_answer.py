from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class InspectionAnswer(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspection_answers", null=True, on_delete=fields.CASCADE)
    inspection = fields.ForeignKeyField("models.Inspection", related_name="answers", on_delete=fields.CASCADE)
    question_key = fields.CharField(max_length=100)
    question_label = fields.CharField(max_length=255)
    answer_type = fields.CharField(max_length=40, default="text")
    value = fields.JSONField(default=dict)
    requires_action = fields.BooleanField(default=False)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspection_answers"
        indexes = (("company_id",), ("inspection_id",), ("question_key",), ("requires_action",))
