from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CondominiumAsset(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="condominium_assets", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="assets", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=140)
    asset_type = fields.CharField(max_length=50, default="other")
    location = fields.CharField(max_length=160, null=True)
    brand = fields.CharField(max_length=100, null=True)
    model = fields.CharField(max_length=100, null=True)
    serial_number = fields.CharField(max_length=100, null=True)
    provider = fields.CharField(max_length=160, null=True)
    installation_date = fields.DateField(null=True)
    requires_maintenance = fields.BooleanField(default=True)
    maintenance_frequency = fields.CharField(max_length=80, null=True)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "condominium_assets"
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("asset_type",),
            ("status",),
            ("serial_number",),
        )
