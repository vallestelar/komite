from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class UnitAnnex(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="unit_annexes", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="unit_annexes", on_delete=fields.CASCADE)
    unit = fields.ForeignKeyField("models.Unit", related_name="annexes", on_delete=fields.CASCADE)
    annex_type = fields.CharField(max_length=40, default="parking")
    identifier = fields.CharField(max_length=80)
    description = fields.CharField(max_length=255, null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "unit_annexes"
        indexes = (("company_id",), ("condominium_id",), ("unit_id",), ("annex_type",), ("status",))
