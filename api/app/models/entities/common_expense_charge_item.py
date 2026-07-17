from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CommonExpenseChargeItem(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="common_expense_charge_items", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="common_expense_charge_items", on_delete=fields.CASCADE)
    charge = fields.ForeignKeyField("models.CommonExpenseCharge", related_name="items", on_delete=fields.CASCADE)
    expense = fields.ForeignKeyField("models.AccountingExpense", related_name="charge_items", on_delete=fields.CASCADE)
    description = fields.TextField()
    expense_amount = fields.DecimalField(max_digits=14, decimal_places=2)
    prorated_amount = fields.DecimalField(max_digits=14, decimal_places=2)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "common_expense_charge_items"
        indexes = (("company_id",), ("condominium_id",), ("charge_id",), ("expense_id",))
