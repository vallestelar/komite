from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Condominium(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="condominiums", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=150)
    address = fields.CharField(max_length=255, null=True)
    commune = fields.CharField(max_length=100, null=True)
    city = fields.CharField(max_length=100, null=True)
    region = fields.CharField(max_length=100, null=True)
    towers_count = fields.IntField(default=0)
    units_count = fields.IntField(default=0)
    status = fields.CharField(max_length=30, default="active")
    communication_rules = fields.JSONField(default=dict)
    incident_categories = fields.JSONField(default=list)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "condominiums"
        indexes = (("company_id", "name"), ("status",))

