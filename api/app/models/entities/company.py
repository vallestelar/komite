from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Company(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=150)
    rut = fields.CharField(max_length=30, null=True, unique=True)
    legal_name = fields.CharField(max_length=180, null=True)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=40, null=True)
    logo_url = fields.CharField(max_length=500, null=True)
    logo_storage_key = fields.CharField(max_length=500, null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "companies"
        indexes = (("name",), ("status",))
