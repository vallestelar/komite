from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class NotificationLog(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="notification_logs", null=True, on_delete=fields.SET_NULL)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="notification_logs", null=True, on_delete=fields.SET_NULL)
    communication = fields.ForeignKeyField("models.Communication", related_name="notification_logs", null=True, on_delete=fields.SET_NULL)
    user = fields.ForeignKeyField("models.User", related_name="notification_logs", null=True, on_delete=fields.SET_NULL)
    channel = fields.CharField(max_length=40)
    destination = fields.CharField(max_length=255, null=True)
    status = fields.CharField(max_length=40, default="pending")
    provider_message_id = fields.CharField(max_length=120, null=True)
    error_message = fields.TextField(null=True)
    sent_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "notification_logs"
        indexes = (("company_id",), ("condominium_id",), ("communication_id",), ("user_id",), ("channel",), ("status",), ("sent_at",))
