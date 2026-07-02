from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AIRequest(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="ai_requests", null=True, on_delete=fields.SET_NULL)
    requested_by = fields.ForeignKeyField("models.User", related_name="ai_requests", null=True, on_delete=fields.SET_NULL)
    provider = fields.CharField(max_length=60)
    model = fields.CharField(max_length=100)
    purpose = fields.CharField(max_length=80)
    input_payload = fields.JSONField(default=dict)
    output_payload = fields.JSONField(null=True)
    status = fields.CharField(max_length=40, default="pending")
    confidence_score = fields.FloatField(null=True)
    error_message = fields.TextField(null=True)
    tokens_input = fields.IntField(null=True)
    tokens_output = fields.IntField(null=True)
    cost_estimate = fields.DecimalField(max_digits=12, decimal_places=4, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "ai_requests"
        indexes = (("condominium_id",), ("purpose",), ("provider", "model"), ("status",), ("created_at",))

