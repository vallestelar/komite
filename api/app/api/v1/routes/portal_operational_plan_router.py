from __future__ import annotations

from datetime import date, time
from math import isfinite
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.core.auth.dependencies import require_access_token
from app.models.entities import Condominium, CondominiumOperationalStaff, PlannedOperationalEvent


router = APIRouter(
    prefix="/api/v1/portal/operational-plan",
    tags=["Portal operational plan"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class PortalOperationalEventOut(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    planned_date: date
    planned_start_time: str | None = None
    planned_end_time: str | None = None
    estimated_duration_hours: float | None = None
    estimated_duration_minutes: int | None = None
    assigned_profile: str | None = None
    assigned_user_id: UUID | None = None
    assigned_user_name: str | None = None
    assigned_user_email: str | None = None
    priority: str
    status: str
    source_type: str | None = None
    section_name: str | None = None
    asset_name: str | None = None
    template_item_id: UUID | None = None
    agenda_order: int = 0


class PortalOperationalPlanSummary(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    overdue: int


class PortalOperationalStaffOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str | None = None
    portal_profile: str
    responsibility: str | None = None
    is_primary: bool


class PortalOperationalPlanResponse(BaseModel):
    condominium_id: UUID
    condominium_name: str
    year: int
    month: int | None = None
    items: list[PortalOperationalEventOut]
    staff: list[PortalOperationalStaffOut]
    summary: PortalOperationalPlanSummary


class PortalOperationalAssignmentRequest(BaseModel):
    assigned_user_id: UUID | None = None


class PortalOperationalScheduleRequest(BaseModel):
    planned_date: date
    planned_start_time: time | None = None


class PortalOperationalEventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    planned_date: date | None = None
    planned_start_time: time | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    priority: str | None = None
    status: str | None = None


class PortalOperationalReorderRequest(BaseModel):
    planned_date: date
    ordered_event_ids: list[UUID]


class PortalUnplannedIncidentRequest(BaseModel):
    title: str
    description: str | None = None
    planned_date: date
    planned_start_time: time | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    priority: str = "medium"


class PortalUnplannedIncidentUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    planned_date: date | None = None
    planned_start_time: time | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    priority: str | None = None
    status: str | None = None


class PortalManualTaskRequest(BaseModel):
    title: str
    description: str | None = None
    planned_date: date
    planned_start_time: time | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    priority: str = "medium"


class PortalManualTaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    planned_date: date | None = None
    planned_start_time: time | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    priority: str | None = None
    status: str | None = None


def _time_to_text(value) -> str | None:
    return value.strftime("%H:%M") if value else None


def _hours_to_minutes(value: float | None) -> int | None:
    if value is None:
        return None
    if not isfinite(value) or value <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La duracion debe ser mayor que 0")
    minutes = round(value * 60)
    if minutes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La duracion debe ser mayor que 0")
    return minutes


def _minutes_to_hours(value: int | None) -> float | None:
    if value is None:
        return None
    return round(value / 60, 2)


def _metadata_value(event: PlannedOperationalEvent, key: str) -> str | None:
    metadata = event.metadata or {}
    value = metadata.get(key)
    return str(value) if value not in (None, "") else None


def _agenda_order(event: PlannedOperationalEvent) -> int:
    metadata = event.metadata or {}
    try:
        return int(metadata.get("agenda_order") or 0)
    except (TypeError, ValueError):
        return 0


def _event_out(event: PlannedOperationalEvent) -> PortalOperationalEventOut:
    assigned_user = getattr(event, "assigned_user", None)
    return PortalOperationalEventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        planned_date=event.planned_date,
        planned_start_time=_time_to_text(event.planned_start_time),
        planned_end_time=_time_to_text(event.planned_end_time),
        estimated_duration_hours=_minutes_to_hours(event.estimated_duration_minutes),
        estimated_duration_minutes=event.estimated_duration_minutes,
        assigned_profile=event.assigned_profile,
        assigned_user_id=event.assigned_user_id,
        assigned_user_name=getattr(assigned_user, "full_name", None),
        assigned_user_email=getattr(assigned_user, "email", None),
        priority=event.priority,
        status=event.status,
        source_type=event.source_type,
        section_name=_metadata_value(event, "section_name"),
        asset_name=_metadata_value(event, "asset_name"),
        template_item_id=event.condominium_template_item_id,
        agenda_order=_agenda_order(event),
    )


def _period_bounds(year: int, month: int | None) -> tuple[date, date]:
    if month:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        return start, end
    return date(year, 1, 1), date(year + 1, 1, 1)


async def _operational_staff(condominium: Condominium, company_id) -> list[CondominiumOperationalStaff]:
    custom_rows = await (
        CondominiumOperationalStaff.filter(
            company_id=company_id,
            condominium_id=condominium.id,
            status="active",
        )
        .select_related("user")
        .order_by("-is_primary", "portal_profile")
    )
    metadata = condominium.metadata or {}
    mode = metadata.get("operational_staff_mode") or ("custom" if custom_rows else "company")
    if mode == "custom":
        rows = custom_rows
    else:
        rows = await (
            CondominiumOperationalStaff.filter(
                company_id=company_id,
                condominium_id__isnull=True,
                status="active",
            )
            .select_related("user")
            .order_by("-is_primary", "portal_profile")
        )
    allowed_profiles = {"project_manager", "supervisor", "ejecutivo", "executive"}
    return [
        row for row in rows
        if (row.portal_profile or "").strip().lower() in allowed_profiles and row.user.status == "active"
    ]


def _staff_out(row: CondominiumOperationalStaff) -> PortalOperationalStaffOut:
    return PortalOperationalStaffOut(
        user_id=row.user_id,
        full_name=row.user.full_name,
        email=row.user.email,
        portal_profile=row.portal_profile,
        responsibility=row.responsibility or row.user.organization_position,
        is_primary=row.is_primary,
    )


async def _current_condominium(request: Request) -> Condominium:
    if not request.state.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene empresa asociada",
        )

    condominium = await Condominium.get_or_none(
        id=request.state.condominium_id,
        company_id=request.state.company_id,
    )
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominio no encontrado para la empresa del usuario",
        )
    return condominium


async def _assign_event_user(
    event: PlannedOperationalEvent,
    condominium: Condominium,
    company_id,
    assigned_user_id: UUID | None,
    *,
    clear: bool = False,
) -> None:
    if assigned_user_id:
        staff = await _operational_staff(condominium, company_id)
        staff_by_user = {row.user_id: row for row in staff}
        selected = staff_by_user.get(assigned_user_id)
        if not selected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no disponible en el equipo operativo de este condominio",
            )
        event.assigned_user_id = selected.user_id
        event.assigned_profile = selected.portal_profile
    elif clear:
        event.assigned_user_id = None
        event.assigned_profile = None


@router.get("/", response_model=PortalOperationalPlanResponse)
async def list_operational_plan(
    request: Request,
    year: int = Query(default_factory=lambda: date.today().year, ge=2020, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    status_filter: str | None = Query(default=None, alias="status"),
) -> PortalOperationalPlanResponse:
    condominium = await _current_condominium(request)

    start_date, end_date = _period_bounds(year, month)
    filters = {
        "company_id": request.state.company_id,
        "condominium_id": request.state.condominium_id,
        "planned_date__gte": start_date,
        "planned_date__lt": end_date,
    }
    if status_filter:
        filters["status"] = status_filter

    events = await (
        PlannedOperationalEvent.filter(**filters)
        .select_related("assigned_user")
        .order_by("planned_date", "priority", "title")
    )
    events.sort(key=lambda event: (event.planned_date, _agenda_order(event), event.priority, event.title))
    staff = await _operational_staff(condominium, request.state.company_id)
    today = date.today()
    summary = PortalOperationalPlanSummary(
        total=len(events),
        pending=sum(1 for event in events if event.status == "pending"),
        in_progress=sum(1 for event in events if event.status == "in_progress"),
        completed=sum(1 for event in events if event.status in ("completed", "done")),
        overdue=sum(1 for event in events if event.status not in ("completed", "done", "cancelled") and event.planned_date < today),
    )

    return PortalOperationalPlanResponse(
        condominium_id=condominium.id,
        condominium_name=condominium.name,
        year=year,
        month=month,
        items=[_event_out(event) for event in events],
        staff=[_staff_out(row) for row in staff],
        summary=summary,
    )


@router.patch("/events/{event_id}/assignment", response_model=PortalOperationalEventOut)
async def assign_operational_event(
    event_id: UUID,
    payload: PortalOperationalAssignmentRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)

    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")

    await _assign_event_user(
        event,
        condominium,
        request.state.company_id,
        payload.assigned_user_id,
        clear=True,
    )

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.patch("/events/reorder", response_model=list[PortalOperationalEventOut])
async def reorder_operational_events(
    payload: PortalOperationalReorderRequest,
    request: Request,
) -> list[PortalOperationalEventOut]:
    if not payload.ordered_event_ids:
        return []

    events = await (
        PlannedOperationalEvent.filter(
            id__in=payload.ordered_event_ids,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .select_related("assigned_user")
    )
    events_by_id = {event.id: event for event in events}
    if len(events_by_id) != len(set(payload.ordered_event_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o mas eventos no existen en este condominio")

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    updated_events: list[PlannedOperationalEvent] = []
    for index, event_id in enumerate(payload.ordered_event_ids):
        event = events_by_id[event_id]
        metadata = dict(event.metadata or {})
        metadata["agenda_order"] = (index + 1) * 1000
        event.planned_date = payload.planned_date
        event.metadata = metadata
        event.updated_by = actor
        await event.save()
        updated_events.append(event)

    return [_event_out(event) for event in updated_events]


@router.patch("/events/{event_id}", response_model=PortalOperationalEventOut)
async def update_operational_event(
    event_id: UUID,
    payload: PortalOperationalEventUpdateRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)

    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El titulo es obligatorio")
        event.title = title
    if "description" in payload.model_fields_set:
        event.description = payload.description.strip() if payload.description else None
    if payload.planned_date is not None:
        event.planned_date = payload.planned_date
    if "planned_start_time" in payload.model_fields_set:
        event.planned_start_time = payload.planned_start_time
    if "estimated_duration_hours" in payload.model_fields_set:
        event.estimated_duration_minutes = _hours_to_minutes(payload.estimated_duration_hours)
    if payload.priority is not None:
        event.priority = payload.priority
    if payload.status is not None:
        event.status = payload.status
    if "assigned_user_id" in payload.model_fields_set:
        await _assign_event_user(
            event,
            condominium,
            request.state.company_id,
            payload.assigned_user_id,
            clear=True,
        )

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.patch("/events/{event_id}/schedule", response_model=PortalOperationalEventOut)
async def reschedule_operational_event(
    event_id: UUID,
    payload: PortalOperationalScheduleRequest,
    request: Request,
) -> PortalOperationalEventOut:
    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")

    event.planned_date = payload.planned_date
    if "planned_start_time" in payload.model_fields_set:
        event.planned_start_time = payload.planned_start_time
    metadata = dict(event.metadata or {})
    metadata["agenda_order"] = int(metadata.get("agenda_order") or 0) or 1000
    event.metadata = metadata

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.delete("/events/{event_id}", status_code=status.HTTP_200_OK)
async def delete_operational_event(
    event_id: UUID,
    request: Request,
) -> dict[str, int]:
    deleted = await PlannedOperationalEvent.filter(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).delete()
    if deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return {"deleted": deleted}


@router.patch("/unplanned-incidents/{event_id}", response_model=PortalOperationalEventOut)
async def update_unplanned_incident_event(
    event_id: UUID,
    payload: PortalUnplannedIncidentUpdateRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)

    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        source_type="unplanned_incident",
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El título es obligatorio")
        event.title = title
    if "description" in payload.model_fields_set:
        event.description = payload.description.strip() if payload.description else None
    if payload.planned_date is not None:
        event.planned_date = payload.planned_date
    if "planned_start_time" in payload.model_fields_set:
        event.planned_start_time = payload.planned_start_time
    if "estimated_duration_hours" in payload.model_fields_set:
        event.estimated_duration_minutes = _hours_to_minutes(payload.estimated_duration_hours)
    if payload.priority is not None:
        event.priority = payload.priority
    if payload.status is not None:
        event.status = payload.status

    if "assigned_user_id" in payload.model_fields_set:
        await _assign_event_user(
            event,
            condominium,
            request.state.company_id,
            payload.assigned_user_id,
            clear=True,
        )

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.post("/unplanned-incidents", response_model=PortalOperationalEventOut, status_code=status.HTTP_201_CREATED)
async def create_unplanned_incident_event(
    payload: PortalUnplannedIncidentRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El título es obligatorio")

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event = await PlannedOperationalEvent.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        title=title,
        description=payload.description.strip() if payload.description else None,
        planned_date=payload.planned_date,
        planned_start_time=payload.planned_start_time,
        estimated_duration_minutes=_hours_to_minutes(payload.estimated_duration_hours),
        priority=payload.priority,
        status="pending",
        source_type="unplanned_incident",
        metadata={
            "section_name": "Incidencia no programada",
            "origin": "portal_admin",
            "created_from": "operational_plan",
        },
        created_by=actor,
        updated_by=actor,
    )
    await _assign_event_user(
        event,
        condominium,
        request.state.company_id,
        payload.assigned_user_id,
    )
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.patch("/manual-tasks/{event_id}", response_model=PortalOperationalEventOut)
async def update_manual_task_event(
    event_id: UUID,
    payload: PortalManualTaskUpdateRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)
    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        source_type="manual_task",
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El titulo es obligatorio")
        event.title = title
    if "description" in payload.model_fields_set:
        event.description = payload.description.strip() if payload.description else None
    if payload.planned_date is not None:
        event.planned_date = payload.planned_date
    if "planned_start_time" in payload.model_fields_set:
        event.planned_start_time = payload.planned_start_time
    if "estimated_duration_hours" in payload.model_fields_set:
        event.estimated_duration_minutes = _hours_to_minutes(payload.estimated_duration_hours)
    if payload.priority is not None:
        event.priority = payload.priority
    if payload.status is not None:
        event.status = payload.status
    if "assigned_user_id" in payload.model_fields_set:
        await _assign_event_user(
            event,
            condominium,
            request.state.company_id,
            payload.assigned_user_id,
            clear=True,
        )

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)


@router.post("/manual-tasks", response_model=PortalOperationalEventOut, status_code=status.HTTP_201_CREATED)
async def create_manual_task_event(
    payload: PortalManualTaskRequest,
    request: Request,
) -> PortalOperationalEventOut:
    condominium = await _current_condominium(request)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El titulo es obligatorio")

    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    event = await PlannedOperationalEvent.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        title=title,
        description=payload.description.strip() if payload.description else None,
        planned_date=payload.planned_date,
        planned_start_time=payload.planned_start_time,
        estimated_duration_minutes=_hours_to_minutes(payload.estimated_duration_hours),
        priority=payload.priority,
        status="pending",
        source_type="manual_task",
        metadata={
            "section_name": "Tarea manual",
            "origin": "portal_admin",
            "created_from": "manual_tasks",
        },
        created_by=actor,
        updated_by=actor,
    )
    await _assign_event_user(
        event,
        condominium,
        request.state.company_id,
        payload.assigned_user_id,
    )
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _event_out(event)
