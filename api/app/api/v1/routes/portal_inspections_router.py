from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from tortoise.timezone import now

from app.core.auth.dependencies import require_access_token
from app.models.entities import OperationalEventExecution, PlannedOperationalEvent


router = APIRouter(
    prefix="/api/v1/portal/inspections",
    tags=["Portal inspections"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class InspectionChecklistItem(BaseModel):
    id: str
    label: str
    status: str = "pending"
    observations: str | None = None
    requires_action: bool = False


class PortalInspectionExecutionOut(BaseModel):
    id: UUID
    result: str
    comments: str | None = None
    requires_follow_up: bool
    executed_at: datetime | None = None
    executed_by_user_id: UUID | None = None
    checklist: list[InspectionChecklistItem] = Field(default_factory=list)


class PortalInspectionOut(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    planned_date: date
    planned_start_time: str | None = None
    assigned_user_id: UUID | None = None
    assigned_user_name: str | None = None
    assigned_profile: str | None = None
    priority: str
    status: str
    event_type: str
    source_type: str | None = None
    section_name: str | None = None
    asset_name: str | None = None
    template_name: str | None = None
    execution: PortalInspectionExecutionOut | None = None


class PortalInspectionSummary(BaseModel):
    total: int
    pending: int
    in_progress: int
    overdue: int
    completed: int
    requires_action: int


class PortalInspectionListResponse(BaseModel):
    items: list[PortalInspectionOut]
    summary: PortalInspectionSummary


class PortalInspectionSaveRequest(BaseModel):
    result: str = "in_progress"
    comments: str | None = None
    requires_follow_up: bool = False
    checklist: list[InspectionChecklistItem] = Field(default_factory=list)
    close_event: bool = False


def _time_to_text(value) -> str | None:
    return value.strftime("%H:%M") if value else None


def _metadata_value(event: PlannedOperationalEvent, key: str) -> str | None:
    metadata = event.metadata or {}
    value = metadata.get(key)
    return str(value) if value not in (None, "") else None


def _default_checklist(event: PlannedOperationalEvent) -> list[InspectionChecklistItem]:
    metadata = event.metadata or {}
    raw_items = metadata.get("checklist")
    if isinstance(raw_items, list):
        items: list[InspectionChecklistItem] = []
        for index, item in enumerate(raw_items):
            if isinstance(item, dict):
                label = str(item.get("label") or item.get("title") or item.get("name") or "").strip()
                if not label:
                    continue
                items.append(InspectionChecklistItem(
                    id=str(item.get("id") or f"item-{index + 1}"),
                    label=label,
                    status=str(item.get("status") or "pending"),
                    observations=item.get("observations"),
                    requires_action=bool(item.get("requires_action") or False),
                ))
        if items:
            return items

    return [
        InspectionChecklistItem(id="main", label=event.title, status="pending"),
    ]


def _execution_out(execution: OperationalEventExecution | None, event: PlannedOperationalEvent) -> PortalInspectionExecutionOut | None:
    if not execution:
        return None
    metadata = execution.metadata or {}
    checklist = metadata.get("checklist")
    if not isinstance(checklist, list):
        checklist = [item.model_dump() for item in _default_checklist(event)]
    return PortalInspectionExecutionOut(
        id=execution.id,
        result=execution.result,
        comments=execution.comments,
        requires_follow_up=execution.requires_follow_up,
        executed_at=execution.executed_at,
        executed_by_user_id=execution.executed_by_user_id,
        checklist=[InspectionChecklistItem(**item) for item in checklist if isinstance(item, dict)],
    )


def _inspection_out(event: PlannedOperationalEvent, execution: OperationalEventExecution | None = None) -> PortalInspectionOut:
    assigned_user = getattr(event, "assigned_user", None)
    return PortalInspectionOut(
        id=event.id,
        title=event.title,
        description=event.description,
        planned_date=event.planned_date,
        planned_start_time=_time_to_text(event.planned_start_time),
        assigned_user_id=event.assigned_user_id,
        assigned_user_name=getattr(assigned_user, "full_name", None),
        assigned_profile=event.assigned_profile,
        priority=event.priority,
        status=event.status,
        event_type=event.event_type,
        source_type=event.source_type,
        section_name=_metadata_value(event, "section_name"),
        asset_name=_metadata_value(event, "asset_name"),
        template_name=_metadata_value(event, "template_name"),
        execution=_execution_out(execution, event),
    )


async def _event_execution(event_id) -> OperationalEventExecution | None:
    return await (
        OperationalEventExecution.filter(event_id=event_id)
        .order_by("-executed_at", "-updated_at")
        .first()
    )


@router.get("/", response_model=PortalInspectionListResponse)
async def list_portal_inspections(
    request: Request,
    year: int = Query(..., ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    status_filter: str | None = Query(default=None, alias="status"),
) -> PortalInspectionListResponse:
    start = date(year, month, 1) if month else date(year, 1, 1)
    if month:
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    else:
        end = date(year + 1, 1, 1)

    filters = {
        "company_id": request.state.company_id,
        "condominium_id": request.state.condominium_id,
        "planned_date__gte": start,
        "planned_date__lt": end,
    }
    if status_filter:
        filters["status"] = status_filter

    events = await (
        PlannedOperationalEvent.filter(**filters)
        .filter(event_type="inspection")
        .select_related("assigned_user")
        .order_by("planned_date", "planned_start_time", "title")
    )
    executions = await OperationalEventExecution.filter(event_id__in=[event.id for event in events]) if events else []
    execution_by_event: dict = {}
    for execution in sorted(executions, key=lambda item: item.updated_at, reverse=True):
        execution_by_event.setdefault(execution.event_id, execution)

    today = date.today()
    items = [_inspection_out(event, execution_by_event.get(event.id)) for event in events]
    summary = PortalInspectionSummary(
        total=len(events),
        pending=sum(1 for event in events if event.status == "pending"),
        in_progress=sum(1 for event in events if event.status == "in_progress"),
        overdue=sum(1 for event in events if event.status not in {"completed", "done", "cancelled"} and event.planned_date < today),
        completed=sum(1 for event in events if event.status in {"completed", "done"}),
        requires_action=sum(1 for execution in execution_by_event.values() if execution.requires_follow_up),
    )
    return PortalInspectionListResponse(items=items, summary=summary)


@router.get("/{event_id}", response_model=PortalInspectionOut)
async def get_portal_inspection(event_id: UUID, request: Request) -> PortalInspectionOut:
    event = await (
        PlannedOperationalEvent.get_or_none(
            id=event_id,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .select_related("assigned_user")
    )
    if not event or event.event_type != "inspection":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspeccion no encontrada")
    return _inspection_out(event, await _event_execution(event.id))


@router.post("/{event_id}/execution", response_model=PortalInspectionOut)
async def save_portal_inspection_execution(
    event_id: UUID,
    payload: PortalInspectionSaveRequest,
    request: Request,
) -> PortalInspectionOut:
    event = await (
        PlannedOperationalEvent.get_or_none(
            id=event_id,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .select_related("assigned_user")
    )
    if not event or event.event_type != "inspection":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspeccion no encontrada")

    result = payload.result or "in_progress"
    if result not in {"pending", "in_progress", "conforme", "observed", "requires_action", "not_executed", "completed"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Resultado de inspeccion no valido")

    checklist = payload.checklist or _default_checklist(event)
    requires_follow_up = payload.requires_follow_up or any(item.requires_action or item.status == "requires_action" for item in checklist)
    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    execution = await _event_execution(event.id)
    executed_at = now() if payload.close_event or result not in {"pending", "in_progress"} else None

    metadata = {
        **((execution.metadata if execution else {}) or {}),
        "checklist": [item.model_dump() for item in checklist],
        "updated_from": "portal_inspections",
    }

    if execution:
        execution.result = result
        execution.comments = payload.comments.strip() if payload.comments else None
        execution.requires_follow_up = requires_follow_up
        execution.executed_by_user_id = request.state.user_id
        execution.executed_at = executed_at or execution.executed_at
        execution.metadata = metadata
        execution.updated_by = actor
        await execution.save()
    else:
        execution = await OperationalEventExecution.create(
            company_id=request.state.company_id,
            event_id=event.id,
            executed_by_user_id=request.state.user_id,
            executed_at=executed_at,
            result=result,
            comments=payload.comments.strip() if payload.comments else None,
            requires_follow_up=requires_follow_up,
            metadata=metadata,
            created_by=actor,
            updated_by=actor,
        )

    if payload.close_event or result in {"conforme", "observed", "requires_action", "not_executed", "completed"}:
        event.status = "completed" if result in {"conforme", "observed", "completed"} else "in_progress"
    else:
        event.status = "in_progress"
    event.updated_by = actor
    await event.save()

    event = await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")
    return _inspection_out(event, execution)
