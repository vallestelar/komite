from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth.dependencies import require_access_token
from app.models.entities import (
    AccountingExpense,
    AccountingIncome,
    AccountingPeriod,
    CommonExpenseCharge,
    CommonExpenseChargeItem,
    CommonExpenseRun,
    Unit,
)

router = APIRouter(
    prefix="/api/v1/portal/accounting",
    tags=["Portal accounting"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _json_money(value: Decimal | int | float | None) -> float:
    return float(_money(value))


def _decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _charge_payload(charge: CommonExpenseCharge) -> dict[str, Any]:
    unit = getattr(charge, "unit", None)
    return {
        "id": str(charge.id),
        "unit_id": str(charge.unit_id),
        "unit_identifier": unit.identifier if unit else "",
        "proration": float(charge.proration or 0),
        "expense_amount": _json_money(charge.expense_amount),
        "reserve_fund_amount": _json_money(charge.reserve_fund_amount),
        "total_amount": _json_money(charge.total_amount),
    }


async def _get_period_for_request(request: Request, period_id: UUID) -> AccountingPeriod:
    period = await AccountingPeriod.get_or_none(id=period_id)
    if not period or str(period.condominium_id) != str(request.state.condominium_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo contable no encontrado")
    return period


@router.get("/summary")
async def get_accounting_summary(request: Request, period_id: UUID):
    period = await _get_period_for_request(request, period_id)
    incomes = await AccountingIncome.filter(period_id=period.id, condominium_id=request.state.condominium_id)
    expenses = await AccountingExpense.filter(period_id=period.id, condominium_id=request.state.condominium_id)
    common_expenses = [expense for expense in expenses if expense.is_common_expense]
    latest_run = (
        await CommonExpenseRun.filter(period_id=period.id, condominium_id=request.state.condominium_id)
        .order_by("-calculated_at", "-created_at")
        .first()
    )
    charge_count = 0
    if latest_run:
        charge_count = await CommonExpenseCharge.filter(run_id=latest_run.id).count()

    total_income = sum((_decimal(item.amount) for item in incomes), Decimal("0"))
    total_expense = sum((_decimal(item.amount) for item in expenses), Decimal("0"))
    common_expense_total = sum((_decimal(item.amount) for item in common_expenses), Decimal("0"))

    return {
        "period": {
            "id": str(period.id),
            "name": period.name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "status": period.status,
            "is_active": period.is_active,
            "reserve_fund_rate": float(period.reserve_fund_rate or 0),
        },
        "totals": {
            "income": _json_money(total_income),
            "expense": _json_money(total_expense),
            "common_expense": _json_money(common_expense_total),
            "balance": _json_money(total_income - total_expense),
        },
        "latest_run": None
        if not latest_run
        else {
            "id": str(latest_run.id),
            "status": latest_run.status,
            "total_expenses": _json_money(latest_run.total_expenses),
            "reserve_fund_rate": float(latest_run.reserve_fund_rate or 0),
            "total_reserve_fund": _json_money(latest_run.total_reserve_fund),
            "total_charged": _json_money(latest_run.total_charged),
            "calculated_at": latest_run.calculated_at.isoformat() if latest_run.calculated_at else None,
            "charge_count": charge_count,
        },
    }


@router.get("/common-expense-runs/latest-charges")
async def get_latest_common_expense_charges(request: Request, period_id: UUID):
    period = await _get_period_for_request(request, period_id)
    latest_run = (
        await CommonExpenseRun.filter(period_id=period.id, condominium_id=request.state.condominium_id)
        .order_by("-calculated_at", "-created_at")
        .first()
    )
    if not latest_run:
        return {"run": None, "charges": []}

    charges = await CommonExpenseCharge.filter(run_id=latest_run.id).select_related("unit")
    sorted_charges = sorted(charges, key=lambda charge: getattr(getattr(charge, "unit", None), "identifier", ""))
    return {
        "run": {
            "id": str(latest_run.id),
            "period_id": str(period.id),
            "status": latest_run.status,
            "total_expenses": _json_money(latest_run.total_expenses),
            "reserve_fund_rate": float(latest_run.reserve_fund_rate or 0),
            "total_reserve_fund": _json_money(latest_run.total_reserve_fund),
            "total_charged": _json_money(latest_run.total_charged),
            "calculated_at": latest_run.calculated_at.isoformat() if latest_run.calculated_at else None,
        },
        "charges": [_charge_payload(charge) for charge in sorted_charges],
    }


@router.post("/common-expense-runs/calculate")
async def calculate_common_expenses(request: Request, period_id: UUID):
    period = await _get_period_for_request(request, period_id)
    units = await Unit.filter(condominium_id=request.state.condominium_id).order_by("identifier")
    expenses = await AccountingExpense.filter(
        period_id=period.id,
        condominium_id=request.state.condominium_id,
        is_common_expense=True,
    ).order_by("expense_date", "created_at")

    if not units:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No hay unidades para calcular gastos comunes")

    run = (
        await CommonExpenseRun.filter(
            period_id=period.id,
            condominium_id=request.state.condominium_id,
            status__in=["draft", "calculated"],
        )
        .order_by("-created_at")
        .first()
    )
    if not run:
        run = await CommonExpenseRun.create(
            company_id=period.company_id,
            condominium_id=period.condominium_id,
            period_id=period.id,
            status="draft",
            reserve_fund_rate=period.reserve_fund_rate or Decimal("0"),
        )
    else:
        existing_charges = await CommonExpenseCharge.filter(run_id=run.id)
        if existing_charges:
            charge_ids = [charge.id for charge in existing_charges]
            await CommonExpenseChargeItem.filter(charge_id__in=charge_ids).delete()
            await CommonExpenseCharge.filter(run_id=run.id).delete()

    reserve_rate = _decimal(period.reserve_fund_rate)
    total_expenses = sum((_decimal(expense.amount) for expense in expenses), Decimal("0"))
    total_reserve = Decimal("0")
    total_charged = Decimal("0")
    charge_rows = []

    for unit in units:
        proration = _decimal(unit.proration_total if unit.proration_total is not None else unit.proration)
        expense_amount = _money((total_expenses * proration) / Decimal("100"))
        reserve_amount = _money(expense_amount * reserve_rate)
        total_amount = expense_amount + reserve_amount
        total_reserve += reserve_amount
        total_charged += total_amount

        charge = await CommonExpenseCharge.create(
            company_id=period.company_id,
            condominium_id=period.condominium_id,
            run_id=run.id,
            period_id=period.id,
            unit_id=unit.id,
            proration=proration,
            expense_amount=expense_amount,
            reserve_fund_amount=reserve_amount,
            total_amount=total_amount,
            status="draft",
        )

        for expense in expenses:
            await CommonExpenseChargeItem.create(
                company_id=period.company_id,
                condominium_id=period.condominium_id,
                charge_id=charge.id,
                expense_id=expense.id,
                description=expense.description,
                expense_amount=expense.amount,
                prorated_amount=_money((_decimal(expense.amount) * proration) / Decimal("100")),
            )

        charge_rows.append(
            {
                "id": str(charge.id),
                "unit_id": str(unit.id),
                "unit_identifier": unit.identifier,
                "proration": float(proration),
                "expense_amount": _json_money(expense_amount),
                "reserve_fund_amount": _json_money(reserve_amount),
                "total_amount": _json_money(total_amount),
            }
        )

    run.status = "calculated"
    run.total_expenses = _money(total_expenses)
    run.reserve_fund_rate = reserve_rate
    run.total_reserve_fund = _money(total_reserve)
    run.total_charged = _money(total_charged)
    run.calculated_at = datetime.now(timezone.utc)
    await run.save()

    return {
        "run": {
            "id": str(run.id),
            "period_id": str(period.id),
            "status": run.status,
            "total_expenses": _json_money(run.total_expenses),
            "reserve_fund_rate": float(run.reserve_fund_rate or 0),
            "total_reserve_fund": _json_money(run.total_reserve_fund),
            "total_charged": _json_money(run.total_charged),
            "calculated_at": run.calculated_at.isoformat() if run.calculated_at else None,
        },
        "charges": charge_rows,
    }
