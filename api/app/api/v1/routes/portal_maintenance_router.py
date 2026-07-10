from calendar import monthrange
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.auth.dependencies import require_access_token
from app.models.entities import (
    CondominiumInspectionItem,
    CondominiumInspectionTemplate,
    OperationalWorkCalendar,
    PlannedOperationalEvent,
)


router = APIRouter(
    prefix="/api/v1/portal/maintenance",
    tags=["Portal maintenance"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class PortalMaintenanceTemplateOut(BaseModel):
    id: UUID
    name: str
    template_type: str
    version: int
    status: str
    effective_from: str | None = None
    effective_to: str | None = None


class PortalMaintenanceItemOut(BaseModel):
    id: UUID
    condominium_template_id: UUID
    section_name: str | None = None
    asset_name: str | None = None
    task_name: str
    instructions: str | None = None
    event_type: str
    periodicity: str | None = None
    planned_months: list = Field(default_factory=list)
    responsible_user_id: UUID | None = None
    responsible_profile: str | None = None
    estimated_duration_minutes: int | None = None
    priority: str
    status: str


class PortalMaintenanceResponse(BaseModel):
    templates: list[PortalMaintenanceTemplateOut]
    selected_template: PortalMaintenanceTemplateOut | None = None
    items: list[PortalMaintenanceItemOut]


class PortalMaintenanceItemUpdate(BaseModel):
    section_name: str | None = Field(default=None, max_length=150)
    asset_name: str | None = Field(default=None, max_length=180)
    task_name: str | None = Field(default=None, max_length=255)
    instructions: str | None = None
    event_type: str | None = Field(default=None, max_length=40)
    periodicity: str | None = Field(default=None, max_length=80)
    planned_months: list | None = None
    responsible_profile: str | None = Field(default=None, max_length=60)
    responsible_user_id: UUID | None = None
    estimated_duration_minutes: int | None = None
    priority: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)


class PortalMaintenanceItemCreate(BaseModel):
    condominium_template_id: UUID
    section_name: str | None = Field(default=None, max_length=150)
    asset_name: str | None = Field(default=None, max_length=180)
    task_name: str = Field(..., max_length=255)
    instructions: str | None = None
    event_type: str = Field(default="maintenance", max_length=40)
    periodicity: str | None = Field(default=None, max_length=80)
    planned_months: list = Field(default_factory=list)
    responsible_profile: str | None = Field(default=None, max_length=60)
    responsible_user_id: UUID | None = None
    estimated_duration_minutes: int | None = None
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="active", max_length=30)


class PortalMaintenanceGenerateRequest(BaseModel):
    condominium_template_id: UUID
    year: int = Field(..., ge=2020, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)
    overwrite_existing: bool = False


class PortalMaintenanceGenerateResponse(BaseModel):
    created: int
    skipped_existing: int
    skipped_inactive: int
    period_label: str


def _template_out(template: CondominiumInspectionTemplate) -> PortalMaintenanceTemplateOut:
    return PortalMaintenanceTemplateOut(
        id=template.id,
        name=template.name,
        template_type=template.template_type,
        version=template.version,
        status=template.status,
        effective_from=template.effective_from.isoformat() if template.effective_from else None,
        effective_to=template.effective_to.isoformat() if template.effective_to else None,
    )


def _item_out(item: CondominiumInspectionItem) -> PortalMaintenanceItemOut:
    return PortalMaintenanceItemOut(
        id=item.id,
        condominium_template_id=item.condominium_template_id,
        section_name=item.section_name,
        asset_name=item.asset_name,
        task_name=item.task_name,
        instructions=item.instructions,
        event_type=item.event_type,
        periodicity=item.periodicity,
        planned_months=item.planned_months or [],
        responsible_user_id=item.responsible_user_id,
        responsible_profile=item.responsible_profile,
        estimated_duration_minutes=item.estimated_duration_minutes,
        priority=item.priority,
        status=item.status,
    )


async def _get_template_or_404(
    template_id: UUID,
    request: Request,
) -> CondominiumInspectionTemplate:
    template = await CondominiumInspectionTemplate.get_or_none(
        id=template_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        template_type__in=("maintenance", "mixed"),
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla del condominio no encontrada")
    return template


def _normalize_months(value: list) -> set[int]:
    months: set[int] = set()
    for item in value or []:
        try:
            month = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= month <= 12:
            months.add(month)
    return months


def _next_business_day(value: date) -> date:
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def _dates_for_item(item: CondominiumInspectionItem, year: int, month: int) -> list[date]:
    periodicity = item.periodicity or "monthly"
    _, days_in_month = monthrange(year, month)

    if periodicity == "daily":
        return [date(year, month, day) for day in range(1, days_in_month + 1) if date(year, month, day).weekday() < 5]

    if periodicity == "weekly":
        first = _next_business_day(date(year, month, 1))
        monday = first + timedelta(days=(0 - first.weekday()) % 7)
        result: list[date] = []
        current = monday
        while current.month == month:
            result.append(current)
            current += timedelta(days=7)
        return result or [first]

    if periodicity == "biweekly":
        return sorted({_next_business_day(date(year, month, 1)), _next_business_day(date(year, month, 15))})

    return [_next_business_day(date(year, month, 1))]


async def _active_calendar(request: Request) -> OperationalWorkCalendar | None:
    return await (
        OperationalWorkCalendar.filter(
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
            status="active",
        )
        .order_by("-effective_from", "name")
        .first()
    )


@router.get("/", response_model=PortalMaintenanceResponse)
async def list_maintenance_plan(
    request: Request,
    template_id: UUID | None = None,
) -> PortalMaintenanceResponse:
    templates = await (
        CondominiumInspectionTemplate.filter(
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
            template_type__in=("maintenance", "mixed"),
        )
        .order_by("-version", "name")
    )

    selected_template = None
    if template_id:
        selected_template = next((item for item in templates if str(item.id) == str(template_id)), None)
        if not selected_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla del condominio no encontrada")
    elif templates:
        selected_template = templates[0]

    items: list[CondominiumInspectionItem] = []
    if selected_template:
        items = await (
            CondominiumInspectionItem.filter(
                company_id=request.state.company_id,
                condominium_id=request.state.condominium_id,
                condominium_template_id=selected_template.id,
            )
            .order_by("section_name", "task_name")
        )

    return PortalMaintenanceResponse(
        templates=[_template_out(template) for template in templates],
        selected_template=_template_out(selected_template) if selected_template else None,
        items=[_item_out(item) for item in items],
    )


@router.post("/items", response_model=PortalMaintenanceItemOut, status_code=status.HTTP_201_CREATED)
async def create_maintenance_item(
    payload: PortalMaintenanceItemCreate,
    request: Request,
) -> PortalMaintenanceItemOut:
    await _get_template_or_404(payload.condominium_template_id, request)
    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    item = await CondominiumInspectionItem.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        condominium_template_id=payload.condominium_template_id,
        section_name=payload.section_name,
        asset_name=payload.asset_name,
        task_name=payload.task_name,
        instructions=payload.instructions,
        event_type=payload.event_type,
        periodicity=payload.periodicity,
        planned_months=payload.planned_months,
        responsible_profile=payload.responsible_profile,
        responsible_user_id=payload.responsible_user_id,
        estimated_duration_minutes=payload.estimated_duration_minutes,
        priority=payload.priority,
        status=payload.status,
        metadata={"created_from_portal": True},
        created_by=actor,
        updated_by=actor,
    )
    return _item_out(item)


@router.patch("/items/{item_id}", response_model=PortalMaintenanceItemOut)
async def update_maintenance_item(
    item_id: UUID,
    payload: PortalMaintenanceItemUpdate,
    request: Request,
) -> PortalMaintenanceItemOut:
    item = await CondominiumInspectionItem.get_or_none(
        id=item_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de mantención no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for field_name, value in data.items():
        setattr(item, field_name, value)
    item.updated_by = getattr(request.state.user, "email", None) or str(request.state.user_id)
    await item.save()
    return _item_out(item)


@router.post("/generate", response_model=PortalMaintenanceGenerateResponse)
async def generate_maintenance_plan(
    payload: PortalMaintenanceGenerateRequest,
    request: Request,
) -> PortalMaintenanceGenerateResponse:
    template = await _get_template_or_404(payload.condominium_template_id, request)
    calendar = await _active_calendar(request)
    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    items = await CondominiumInspectionItem.filter(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        condominium_template_id=template.id,
    )
    months = [payload.month] if payload.month else list(range(1, 13))
    created = 0
    skipped_existing = 0
    skipped_inactive = 0

    for item in items:
        if item.status != "active":
            skipped_inactive += 1
            continue

        planned_months = _normalize_months(item.planned_months)
        item_months = [month for month in months if not planned_months or month in planned_months]
        for month in item_months:
            for planned_date in _dates_for_item(item, payload.year, month):
                if planned_date.year != payload.year or planned_date.month != month:
                    continue

                existing = await PlannedOperationalEvent.get_or_none(
                    company_id=request.state.company_id,
                    condominium_id=request.state.condominium_id,
                    condominium_template_item_id=item.id,
                    planned_date=planned_date,
                    source_type="maintenance_template",
                )
                if existing and not payload.overwrite_existing:
                    skipped_existing += 1
                    continue
                if existing and payload.overwrite_existing:
                    existing.title = item.task_name
                    existing.description = item.instructions
                    existing.assigned_profile = item.responsible_profile
                    existing.priority = item.priority
                    existing.status = "pending"
                    existing.event_type = item.event_type or "maintenance"
                    existing.calendar_id = calendar.id if calendar else None
                    existing.metadata = {
                        **(existing.metadata or {}),
                        "section_name": item.section_name,
                        "asset_name": item.asset_name,
                        "template_id": str(template.id),
                        "regenerated_from_portal": True,
                    }
                    existing.updated_by = actor
                    await existing.save()
                    continue

                await PlannedOperationalEvent.create(
                    company_id=request.state.company_id,
                    condominium_id=request.state.condominium_id,
                    condominium_template_item_id=item.id,
                    calendar_id=calendar.id if calendar else None,
                    title=item.task_name,
                    description=item.instructions,
                    planned_date=planned_date,
                    assigned_profile=item.responsible_profile,
                    priority=item.priority,
                    status="pending",
                    event_type=item.event_type or "maintenance",
                    source_type="maintenance_template",
                    source_id=template.id,
                    metadata={
                        "section_name": item.section_name,
                        "asset_name": item.asset_name,
                        "template_id": str(template.id),
                        "template_name": template.name,
                        "generated_from_portal": True,
                    },
                    created_by=actor,
                    updated_by=actor,
                )
                created += 1

    period_label = f"{payload.month:02d}/{payload.year}" if payload.month else str(payload.year)
    return PortalMaintenanceGenerateResponse(
        created=created,
        skipped_existing=skipped_existing,
        skipped_inactive=skipped_inactive,
        period_label=period_label,
    )


@router.post("/items/{item_id}/deactivate", response_model=PortalMaintenanceItemOut)
async def deactivate_maintenance_item(
    item_id: UUID,
    request: Request,
) -> PortalMaintenanceItemOut:
    item = await CondominiumInspectionItem.get_or_none(
        id=item_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).select_related("condominium_template")
    if not item or item.condominium_template.template_type not in ("maintenance", "mixed"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de mantención no encontrado")

    item.status = "inactive"
    item.updated_by = getattr(request.state.user, "email", None) or str(request.state.user_id)
    await item.save()
    return _item_out(item)
