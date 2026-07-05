from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class User(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="users", null=True, on_delete=fields.SET_NULL)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255, null=True)
    full_name = fields.CharField(max_length=150)
    phone = fields.CharField(max_length=40, null=True)
    document_type = fields.CharField(max_length=30, null=True)
    document_number = fields.CharField(max_length=40, null=True)
    address = fields.CharField(max_length=255, null=True)
    status = fields.CharField(max_length=30, default="active")
    company_profile = fields.CharField(max_length=60, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "users"
        indexes = (("email",), ("company_id",), ("document_number",), ("company_profile",), ("status",))
