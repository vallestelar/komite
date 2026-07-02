from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Building(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="buildings", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=100)
    floors_count = fields.IntField(default=0)
    units_count = fields.IntField(default=0)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "buildings"
        indexes = (("condominium_id", "name"),)

