from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalNotification(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_notifications", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="operational_notifications", on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="operational_notifications", null=True, on_delete=fields.SET_NULL)
    external_service_order = fields.ForeignKeyField("models.ExternalServiceOrder", related_name="operational_notifications", null=True, on_delete=fields.SET_NULL)
    ai_request = fields.ForeignKeyField("models.AIRequest", related_name="operational_notifications", null=True, on_delete=fields.SET_NULL)
    report = fields.ForeignKeyField("models.Report", related_name="operational_notifications", null=True, on_delete=fields.SET_NULL)
    assigned_to = fields.ForeignKeyField("models.User", related_name="assigned_operational_notifications", null=True, on_delete=fields.SET_NULL)
    validated_by = fields.ForeignKeyField("models.User", related_name="validated_operational_notifications", null=True, on_delete=fields.SET_NULL)
    source_type = fields.CharField(max_length=60, default="external_service_order")
    source_id = fields.CharField(max_length=80, null=True)
    title = fields.CharField(max_length=180)
    summary = fields.TextField(null=True)
    body = fields.TextField(null=True)
    draft_body = fields.TextField(null=True)
    final_body = fields.TextField(null=True)
    status = fields.CharField(max_length=40, default="pending_review")
    priority = fields.CharField(max_length=30, default="medium")
    send_status = fields.CharField(max_length=40, default="not_ready")
    send_channel = fields.CharField(max_length=40, default="mobile_app")
    mobile_payload = fields.JSONField(default=dict)
    validated_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_notifications"
        indexes = (
            ("company_id",),
            ("condominium_id", "status"),
            ("event_id",),
            ("external_service_order_id",),
            ("assigned_to_id", "status"),
            ("validated_by_id",),
            ("report_id",),
            ("priority",),
            ("send_status",),
        )
