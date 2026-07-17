from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingIncome(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_incomes", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_incomes", on_delete=fields.CASCADE)
    period = fields.ForeignKeyField("models.AccountingPeriod", related_name="incomes", on_delete=fields.CASCADE)
    unit = fields.ForeignKeyField("models.Unit", related_name="accounting_incomes", null=True, on_delete=fields.SET_NULL)
    income_type = fields.ForeignKeyField("models.AccountingIncomeType", related_name="incomes", null=True, on_delete=fields.SET_NULL)
    bank = fields.ForeignKeyField("models.Bank", related_name="accounting_incomes", null=True, on_delete=fields.SET_NULL)
    income_date = fields.DateField()
    description = fields.TextField()
    amount = fields.DecimalField(max_digits=14, decimal_places=2)
    payment_method = fields.CharField(max_length=60, null=True)
    status = fields.CharField(max_length=30, default="confirmed")
    reference = fields.CharField(max_length=120, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "accounting_incomes"
        indexes = (("company_id",), ("condominium_id", "period_id"), ("unit_id",), ("income_type_id",), ("bank_id",), ("income_date",), ("status",))
