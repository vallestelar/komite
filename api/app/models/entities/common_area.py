from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CommonArea(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="common_areas", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="common_areas", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=120)
    area_type = fields.CharField(max_length=40, default="other")
    location = fields.CharField(max_length=160, null=True)
    capacity = fields.IntField(null=True)
    requires_reservation = fields.BooleanField(default=False)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "common_areas"
        indexes = (("company_id",), ("condominium_id",), ("area_type",), ("status",))
