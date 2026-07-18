from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingSupplier(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_suppliers", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_suppliers", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=180)
    rut = fields.CharField(max_length=30, null=True)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=40, null=True)
    supplier_category = fields.ForeignKeyField("models.AccountingSupplierCategory", related_name="suppliers", null=True, on_delete=fields.SET_NULL)
    category = fields.CharField(max_length=80, null=True)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_suppliers"
        indexes = (("company_id",), ("condominium_id",), ("supplier_category_id",), ("name",), ("status",))
