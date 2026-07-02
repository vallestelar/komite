from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AuditLog(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="audit_logs", null=True, on_delete=fields.SET_NULL)
    user = fields.ForeignKeyField("models.User", related_name="audit_logs", null=True, on_delete=fields.SET_NULL)
    action = fields.CharField(max_length=100)
    entity_type = fields.CharField(max_length=80)
    entity_id = fields.UUIDField(null=True)
    previous_state = fields.JSONField(null=True)
    new_state = fields.JSONField(null=True)
    ip_address = fields.CharField(max_length=80, null=True)
    user_agent = fields.CharField(max_length=255, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "audit_logs"
        indexes = (("condominium_id",), ("user_id",), ("entity_type", "entity_id"), ("action",), ("created_at",))

