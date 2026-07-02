from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Bank(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=120, unique=True)
    code = fields.CharField(max_length=40, null=True, unique=True)
    country = fields.CharField(max_length=80, default="Chile")
    website = fields.CharField(max_length=255, null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "banks"
        indexes = (("name",), ("code",), ("status",))
