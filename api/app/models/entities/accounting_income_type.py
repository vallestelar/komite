from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingIncomeType(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_income_types", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_income_types", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=120)
    code = fields.CharField(max_length=60, null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_income_types"
        indexes = (("company_id",), ("condominium_id",), ("name",), ("status",))
