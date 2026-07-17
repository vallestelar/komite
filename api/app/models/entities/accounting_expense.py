from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingExpense(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_expenses", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_expenses", on_delete=fields.CASCADE)
    period = fields.ForeignKeyField("models.AccountingPeriod", related_name="expenses", on_delete=fields.CASCADE)
    supplier = fields.ForeignKeyField("models.AccountingSupplier", related_name="expenses", null=True, on_delete=fields.SET_NULL)
    attachment = fields.ForeignKeyField("models.Attachment", related_name="accounting_expenses", null=True, on_delete=fields.SET_NULL)
    expense_date = fields.DateField()
    description = fields.TextField()
    amount = fields.DecimalField(max_digits=14, decimal_places=2)
    category = fields.CharField(max_length=80, null=True)
    document_number = fields.CharField(max_length=120, null=True)
    is_common_expense = fields.BooleanField(default=True)
    status = fields.CharField(max_length=30, default="approved")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_expenses"
        indexes = (("company_id",), ("condominium_id", "period_id"), ("supplier_id",), ("expense_date",), ("category",), ("status",))
