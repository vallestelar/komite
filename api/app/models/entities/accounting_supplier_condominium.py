from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingSupplierCondominium(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_supplier_condominiums", null=True, on_delete=fields.CASCADE)
    supplier = fields.ForeignKeyField("models.AccountingSupplier", related_name="condominium_links", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_supplier_links", on_delete=fields.CASCADE)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_supplier_condominiums"
        unique_together = (("supplier_id", "condominium_id"),)
        indexes = (("company_id",), ("supplier_id",), ("condominium_id",), ("status",))
