from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class UnitPet(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="unit_pets", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="unit_pets", on_delete=fields.CASCADE)
    unit = fields.ForeignKeyField("models.Unit", related_name="pets", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=120)
    species = fields.CharField(max_length=40, default="dog")
    breed = fields.CharField(max_length=120, null=True)
    color = fields.CharField(max_length=80, null=True)
    chip_number = fields.CharField(max_length=80, null=True)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "unit_pets"
        indexes = (("company_id",), ("condominium_id",), ("unit_id",), ("species",), ("status",), ("chip_number",))
