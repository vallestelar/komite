from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CommunicationRecipient(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    communication = fields.ForeignKeyField("models.Communication", related_name="recipients", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="communication_recipients", null=True, on_delete=fields.SET_NULL)
    unit = fields.ForeignKeyField("models.Unit", related_name="communication_recipients", null=True, on_delete=fields.SET_NULL)
    recipient_type = fields.CharField(max_length=40, default="user")
    channel = fields.CharField(max_length=40)
    destination = fields.CharField(max_length=255, null=True)
    delivery_status = fields.CharField(max_length=40, default="pending")
    delivered_at = fields.DatetimeField(null=True)
    read_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "communication_recipients"
        indexes = (("communication_id",), ("user_id",), ("channel",), ("delivery_status",))

