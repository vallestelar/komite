from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AccountingPeriod(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="accounting_periods", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="accounting_periods", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=120)
    description = fields.TextField(null=True)
    start_date = fields.DateField()
    end_date = fields.DateField()
    status = fields.CharField(max_length=30, default="draft")
    is_active = fields.BooleanField(default=False)
    reserve_fund_rate = fields.DecimalField(max_digits=7, decimal_places=4, default=0)
    closed_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    async def save(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValueError("La fecha de fin del periodo no puede ser anterior a la fecha de inicio")
        if self.condominium_id:
            overlapping = (
                await AccountingPeriod.filter(
                    condominium_id=self.condominium_id,
                    start_date__lte=self.end_date,
                    end_date__gte=self.start_date,
                )
                .exclude(id=self.id)
                .first()
            )
            if overlapping:
                raise ValueError(
                    f"El periodo se solapa con {overlapping.name} ({overlapping.start_date:%d/%m/%Y} - {overlapping.end_date:%d/%m/%Y})"
                )
        if self.is_active:
            self.status = "open"
        if self.status in {"closed", "blocked", "cancelled"}:
            self.is_active = False
        await super().save(*args, **kwargs)
        if self.is_active and self.condominium_id:
            await AccountingPeriod.filter(condominium_id=self.condominium_id, is_active=True).exclude(id=self.id).update(
                is_active=False,
                status="draft",
            )

    async def delete(self, *args, **kwargs):
        from app.models.entities.accounting_expense import AccountingExpense
        from app.models.entities.accounting_income import AccountingIncome
        from app.models.entities.common_expense_run import CommonExpenseRun

        usage_count = (
            await AccountingIncome.filter(period_id=self.id).count()
            + await AccountingExpense.filter(period_id=self.id).count()
            + await CommonExpenseRun.filter(period_id=self.id).count()
        )
        if usage_count:
            raise ValueError("No se puede eliminar un periodo que ya tiene ingresos, egresos o calculos de gasto comun")
        return await super().delete(*args, **kwargs)

    class Meta:
        table = "accounting_periods"
        indexes = (("company_id",), ("condominium_id", "status"), ("condominium_id", "start_date"), ("is_active",))
