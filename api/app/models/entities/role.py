from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Role(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    code = fields.CharField(max_length=60, unique=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    permissions = fields.JSONField(default=dict)
    is_system = fields.BooleanField(default=True)

    class Meta:
        table = "roles"
        indexes = (("code",),)

