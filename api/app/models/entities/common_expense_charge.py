from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CommonExpenseCharge(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="common_expense_charges", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="common_expense_charges", on_delete=fields.CASCADE)
    run = fields.ForeignKeyField("models.CommonExpenseRun", related_name="charges", on_delete=fields.CASCADE)
    period = fields.ForeignKeyField("models.AccountingPeriod", related_name="common_expense_charges", on_delete=fields.CASCADE)
    unit = fields.ForeignKeyField("models.Unit", related_name="common_expense_charges", on_delete=fields.CASCADE)
    proration = fields.DecimalField(max_digits=12, decimal_places=6, default=0)
    expense_amount = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    reserve_fund_amount = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = fields.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = fields.CharField(max_length=30, default="draft")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "common_expense_charges"
        indexes = (("company_id",), ("condominium_id", "period_id"), ("run_id",), ("unit_id",), ("status",))
        unique_together = (("run_id", "unit_id"),)
