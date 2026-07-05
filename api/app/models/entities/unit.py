from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Unit(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="units", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="units", on_delete=fields.CASCADE)
    building = fields.ForeignKeyField("models.Building", related_name="units", null=True, on_delete=fields.SET_NULL)
    identifier = fields.TextField()
    floor = fields.CharField(max_length=20, null=True)
    unit_type = fields.CharField(max_length=30, default="apartment")
    external_code = fields.TextField(null=True)
    allocation_number = fields.IntField(null=True)
    allocation_identifier = fields.TextField(null=True)
    proration_total = fields.DecimalField(max_digits=12, decimal_places=6, null=True)
    proration = fields.DecimalField(max_digits=12, decimal_places=6, null=True)
    assignment_date = fields.DateField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "units"
        indexes = (("company_id",), ("condominium_id", "identifier"), ("condominium_id", "external_code"), ("building_id",))
