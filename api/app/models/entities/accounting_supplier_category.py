from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingSupplierCategory(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_supplier_categories", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=120)
    code = fields.CharField(max_length=80, null=True)
    status = fields.CharField(max_length=30, default="active")
    display_order = fields.IntField(default=0)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_supplier_categories"
        unique_together = (("company_id", "code"),)
        indexes = (("company_id",), ("name",), ("code",), ("status",))
