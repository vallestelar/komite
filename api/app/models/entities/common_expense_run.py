from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CommonExpenseRun(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="common_expense_runs", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="common_expense_runs", on_delete=fields.CASCADE)
    period = fields.ForeignKeyField("models.AccountingPeriod", related_name="common_expense_runs", on_delete=fields.CASCADE)
    status = fields.CharField(max_length=30, default="draft")
    total_expenses = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    reserve_fund_rate = fields.DecimalField(max_digits=7, decimal_places=4, default=0)
    total_reserve_fund = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_charged = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    calculated_at = fields.DatetimeField(null=True)
    published_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "common_expense_runs"
        indexes = (("company_id",), ("condominium_id", "period_id"), ("status",), ("calculated_at",))
