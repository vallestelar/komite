from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Unit(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="units", on_delete=fields.CASCADE)
    building = fields.ForeignKeyField("models.Building", related_name="units", null=True, on_delete=fields.SET_NULL)
    identifier = fields.CharField(max_length=80)
    floor = fields.CharField(max_length=20, null=True)
    unit_type = fields.CharField(max_length=30, default="apartment")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "units"
        indexes = (("condominium_id", "identifier"), ("building_id",))

