from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class ExternalServiceOrder(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="external_service_orders", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="external_service_orders", on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="external_service_orders", on_delete=fields.CASCADE)
    asset = fields.ForeignKeyField("models.CondominiumAsset", related_name="external_service_orders", null=True, on_delete=fields.SET_NULL)
    execution = fields.ForeignKeyField("models.OperationalEventExecution", related_name="external_service_orders", null=True, on_delete=fields.SET_NULL)
    ai_prompt_template = fields.ForeignKeyField("models.AIPromptTemplate", related_name="external_service_orders", null=True, on_delete=fields.SET_NULL)
    ai_request = fields.ForeignKeyField("models.AIRequest", related_name="external_service_orders", null=True, on_delete=fields.SET_NULL)
    report = fields.ForeignKeyField("models.Report", related_name="external_service_orders", null=True, on_delete=fields.SET_NULL)
    token_hash = fields.CharField(max_length=128, unique=True)
    title = fields.CharField(max_length=180)
    instructions = fields.TextField(null=True)
    provider_name = fields.CharField(max_length=160)
    provider_email = fields.CharField(max_length=255, null=True)
    provider_phone = fields.CharField(max_length=40, null=True)
    prompt_key = fields.CharField(max_length=120, default="vendor_service_report")
    status = fields.CharField(max_length=40, default="pending")
    expires_at = fields.DatetimeField(null=True)
    submitted_at = fields.DatetimeField(null=True)
    submission_payload = fields.JSONField(default=dict)
    ai_generated_text = fields.TextField(null=True)
    public_url = fields.CharField(max_length=500, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "external_service_orders"
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("event_id",),
            ("asset_id",),
            ("execution_id",),
            ("ai_prompt_template_id",),
            ("status",),
            ("expires_at",),
            ("submitted_at",),
        )
