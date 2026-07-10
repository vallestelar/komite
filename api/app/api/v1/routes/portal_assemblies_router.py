from __future__ import annotations

from datetime import date, time
from io import BytesIO
from math import isfinite
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.auth.dependencies import require_access_token
from app.models.entities import Assembly, Condominium, PlannedOperationalEvent


router = APIRouter(
    prefix="/api/v1/portal/assemblies",
    tags=["Portal assemblies"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)

ASSEMBLY_STATUSES = {"scheduled", "in_progress", "closed", "cancelled"}
ASSEMBLY_TYPES = {"ordinary", "extraordinary", "committee", "informative"}
ASSEMBLY_MODALITIES = {"presential", "online", "hybrid"}


class AssemblyAttendee(BaseModel):
    name: str
    email: str | None = None
    role: str | None = None
    attendance_status: str = "expected"
    notes: str | None = None


class AssemblyAgendaItem(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    owner: str | None = None
    conclusion: str | None = None
    status: str = "pending"


class PortalAssemblyEventOut(BaseModel):
    id: UUID
    title: str
    planned_date: date
    planned_start_time: str | None = None
    estimated_duration_hours: float | None = None
    assigned_user_id: UUID | None = None
    assigned_user_name: str | None = None
    priority: str
    status: str
    event_type: str
    source_type: str | None = None
    source_id: UUID | None = None


class PortalAssemblyOut(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    assembly_type: str
    status: str
    scheduled_date: date
    scheduled_start_time: str | None = None
    estimated_duration_hours: float | None = None
    location: str | None = None
    modality: str
    quorum_required: int | None = None
    attendees: list[AssemblyAttendee] = Field(default_factory=list)
    agenda_items: list[AssemblyAgendaItem] = Field(default_factory=list)
    conclusions: str | None = None
    event: PortalAssemblyEventOut | None = None


class PortalAssemblyListResponse(BaseModel):
    items: list[PortalAssemblyOut]
    summary: dict[str, int]


class PortalAssemblyCreateRequest(BaseModel):
    title: str
    description: str | None = None
    assembly_type: str = "ordinary"
    status: str = "scheduled"
    scheduled_date: date
    scheduled_start_time: time | None = None
    estimated_duration_hours: float | None = None
    location: str | None = None
    modality: str = "presential"
    quorum_required: int | None = None
    attendees: list[AssemblyAttendee] = Field(default_factory=list)
    agenda_items: list[AssemblyAgendaItem] = Field(default_factory=list)
    conclusions: str | None = None


class PortalAssemblyUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    assembly_type: str | None = None
    status: str | None = None
    scheduled_date: date | None = None
    scheduled_start_time: time | None = None
    estimated_duration_hours: float | None = None
    location: str | None = None
    modality: str | None = None
    quorum_required: int | None = None
    attendees: list[AssemblyAttendee] | None = None
    agenda_items: list[AssemblyAgendaItem] | None = None
    conclusions: str | None = None


async def _current_condominium(request: Request) -> Condominium:
    condominium = await Condominium.get_or_none(
        id=request.state.condominium_id,
        company_id=request.state.company_id,
    )
    if not condominium:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condominio no encontrado")
    return condominium


def _actor(request: Request) -> str:
    return getattr(request.state.user, "email", None) or str(request.state.user_id)


def _time_to_text(value) -> str | None:
    return value.strftime("%H:%M") if value else None


def _hours_to_minutes(value: float | None) -> int | None:
    if value is None:
        return None
    if not isfinite(value) or value <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La duración debe ser mayor que 0")
    return max(1, round(value * 60))


def _minutes_to_hours(value: int | None) -> float | None:
    return round(value / 60, 2) if value else None


def _normalize_choice(value: str | None, allowed: set[str], field_name: str, default: str) -> str:
    normalized = (value or default).strip().lower()
    if normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field_name} no permitido")
    return normalized


def _clean_attendees(items: list[AssemblyAttendee]) -> list[dict]:
    cleaned: list[dict] = []
    for item in items:
        name = item.name.strip()
        if not name:
            continue
        cleaned.append({
            "name": name,
            "email": item.email.strip() if item.email else None,
            "role": item.role.strip() if item.role else None,
            "attendance_status": item.attendance_status or "expected",
            "notes": item.notes.strip() if item.notes else None,
        })
    return cleaned


def _clean_agenda_items(items: list[AssemblyAgendaItem]) -> list[dict]:
    cleaned: list[dict] = []
    for index, item in enumerate(items):
        title = item.title.strip()
        if not title:
            continue
        cleaned.append({
            "id": item.id or f"point-{index + 1}",
            "title": title,
            "description": item.description.strip() if item.description else None,
            "owner": item.owner.strip() if item.owner else None,
            "conclusion": item.conclusion.strip() if item.conclusion else None,
            "status": item.status or "pending",
        })
    return cleaned


def _event_out(event: PlannedOperationalEvent | None) -> PortalAssemblyEventOut | None:
    if not event:
        return None
    assigned_user = getattr(event, "assigned_user", None)
    return PortalAssemblyEventOut(
        id=event.id,
        title=event.title,
        planned_date=event.planned_date,
        planned_start_time=_time_to_text(event.planned_start_time),
        estimated_duration_hours=_minutes_to_hours(event.estimated_duration_minutes),
        assigned_user_id=event.assigned_user_id,
        assigned_user_name=getattr(assigned_user, "full_name", None),
        priority=event.priority,
        status=event.status,
        event_type=event.event_type,
        source_type=event.source_type,
        source_id=event.source_id,
    )


def _assembly_out(assembly: Assembly) -> PortalAssemblyOut:
    event = getattr(assembly, "event", None)
    return PortalAssemblyOut(
        id=assembly.id,
        title=assembly.title,
        description=assembly.description,
        assembly_type=assembly.assembly_type,
        status=assembly.status,
        scheduled_date=assembly.scheduled_date,
        scheduled_start_time=_time_to_text(assembly.scheduled_start_time),
        estimated_duration_hours=_minutes_to_hours(assembly.estimated_duration_minutes),
        location=assembly.location,
        modality=assembly.modality,
        quorum_required=assembly.quorum_required,
        attendees=[AssemblyAttendee(**item) for item in (assembly.attendees or []) if isinstance(item, dict)],
        agenda_items=[AssemblyAgendaItem(**item) for item in (assembly.agenda_items or []) if isinstance(item, dict)],
        conclusions=assembly.conclusions,
        event=_event_out(event),
    )


def _status_to_event_status(value: str) -> str:
    if value == "closed":
        return "completed"
    if value == "cancelled":
        return "cancelled"
    if value == "in_progress":
        return "in_progress"
    return "pending"


async def _sync_event_from_assembly(assembly: Assembly, actor: str) -> PlannedOperationalEvent:
    event = await PlannedOperationalEvent.get_or_none(id=assembly.event_id) if assembly.event_id else None
    metadata = {
        "section_name": "Asamblea",
        "assembly_type": assembly.assembly_type,
        "modality": assembly.modality,
        "location": assembly.location,
        "agenda_points": len(assembly.agenda_items or []),
        "attendees": len(assembly.attendees or []),
    }
    if event:
        event.title = assembly.title
        event.description = assembly.description
        event.planned_date = assembly.scheduled_date
        event.planned_start_time = assembly.scheduled_start_time
        event.estimated_duration_minutes = assembly.estimated_duration_minutes
        event.status = _status_to_event_status(assembly.status)
        event.event_type = "assembly"
        event.source_type = "assembly"
        event.source_id = assembly.id
        event.metadata = {**(event.metadata or {}), **metadata}
        event.updated_by = actor
        await event.save()
    else:
        event = await PlannedOperationalEvent.create(
            company_id=assembly.company_id,
            condominium_id=assembly.condominium_id,
            title=assembly.title,
            description=assembly.description,
            planned_date=assembly.scheduled_date,
            planned_start_time=assembly.scheduled_start_time,
            estimated_duration_minutes=assembly.estimated_duration_minutes,
            priority="medium",
            status=_status_to_event_status(assembly.status),
            event_type="assembly",
            source_type="assembly",
            source_id=assembly.id,
            metadata=metadata,
            created_by=actor,
            updated_by=actor,
        )
        assembly.event_id = event.id
        assembly.updated_by = actor
        await assembly.save()
    return await PlannedOperationalEvent.get(id=event.id).select_related("assigned_user")


@router.get("/", response_model=PortalAssemblyListResponse)
async def list_assemblies(
    request: Request,
    year: int = Query(default_factory=lambda: date.today().year, ge=2020, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    status_filter: str | None = Query(default=None, alias="status"),
) -> PortalAssemblyListResponse:
    await _current_condominium(request)
    start = date(year, month, 1) if month else date(year, 1, 1)
    end = date(year + 1, 1, 1) if (month == 12 or not month) else date(year, month + 1, 1)
    filters = {
        "company_id": request.state.company_id,
        "condominium_id": request.state.condominium_id,
        "scheduled_date__gte": start,
        "scheduled_date__lt": end,
    }
    if status_filter:
        filters["status"] = status_filter
    assemblies = await (
        Assembly.filter(**filters)
        .select_related("event", "event__assigned_user")
        .order_by("scheduled_date", "scheduled_start_time", "title")
    )
    summary = {
        "total": len(assemblies),
        "scheduled": sum(1 for item in assemblies if item.status == "scheduled"),
        "in_progress": sum(1 for item in assemblies if item.status == "in_progress"),
        "closed": sum(1 for item in assemblies if item.status == "closed"),
        "cancelled": sum(1 for item in assemblies if item.status == "cancelled"),
    }
    return PortalAssemblyListResponse(items=[_assembly_out(item) for item in assemblies], summary=summary)


@router.get("/{assembly_id}", response_model=PortalAssemblyOut)
async def get_assembly(assembly_id: UUID, request: Request) -> PortalAssemblyOut:
    assembly = await (
        Assembly.get_or_none(
            id=assembly_id,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .select_related("event", "event__assigned_user")
    )
    if not assembly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asamblea no encontrada")
    return _assembly_out(assembly)


@router.post("/", response_model=PortalAssemblyOut, status_code=status.HTTP_201_CREATED)
async def create_assembly(payload: PortalAssemblyCreateRequest, request: Request) -> PortalAssemblyOut:
    await _current_condominium(request)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El título es obligatorio")
    actor = _actor(request)
    assembly = await Assembly.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        title=title,
        description=payload.description.strip() if payload.description else None,
        assembly_type=_normalize_choice(payload.assembly_type, ASSEMBLY_TYPES, "Tipo de asamblea", "ordinary"),
        status=_normalize_choice(payload.status, ASSEMBLY_STATUSES, "Estado", "scheduled"),
        scheduled_date=payload.scheduled_date,
        scheduled_start_time=payload.scheduled_start_time,
        estimated_duration_minutes=_hours_to_minutes(payload.estimated_duration_hours),
        location=payload.location.strip() if payload.location else None,
        modality=_normalize_choice(payload.modality, ASSEMBLY_MODALITIES, "Modalidad", "presential"),
        quorum_required=payload.quorum_required,
        attendees=_clean_attendees(payload.attendees),
        agenda_items=_clean_agenda_items(payload.agenda_items),
        conclusions=payload.conclusions.strip() if payload.conclusions else None,
        created_by=actor,
        updated_by=actor,
    )
    await _sync_event_from_assembly(assembly, actor)
    assembly = await Assembly.get(id=assembly.id).select_related("event", "event__assigned_user")
    return _assembly_out(assembly)


@router.patch("/{assembly_id}", response_model=PortalAssemblyOut)
async def update_assembly(assembly_id: UUID, payload: PortalAssemblyUpdateRequest, request: Request) -> PortalAssemblyOut:
    assembly = await Assembly.get_or_none(
        id=assembly_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not assembly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asamblea no encontrada")

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El título es obligatorio")
        assembly.title = title
    if "description" in payload.model_fields_set:
        assembly.description = payload.description.strip() if payload.description else None
    if payload.assembly_type is not None:
        assembly.assembly_type = _normalize_choice(payload.assembly_type, ASSEMBLY_TYPES, "Tipo de asamblea", assembly.assembly_type)
    if payload.status is not None:
        assembly.status = _normalize_choice(payload.status, ASSEMBLY_STATUSES, "Estado", assembly.status)
    if payload.scheduled_date is not None:
        assembly.scheduled_date = payload.scheduled_date
    if "scheduled_start_time" in payload.model_fields_set:
        assembly.scheduled_start_time = payload.scheduled_start_time
    if "estimated_duration_hours" in payload.model_fields_set:
        assembly.estimated_duration_minutes = _hours_to_minutes(payload.estimated_duration_hours)
    if "location" in payload.model_fields_set:
        assembly.location = payload.location.strip() if payload.location else None
    if payload.modality is not None:
        assembly.modality = _normalize_choice(payload.modality, ASSEMBLY_MODALITIES, "Modalidad", assembly.modality)
    if "quorum_required" in payload.model_fields_set:
        assembly.quorum_required = payload.quorum_required
    if payload.attendees is not None:
        assembly.attendees = _clean_attendees(payload.attendees)
    if payload.agenda_items is not None:
        assembly.agenda_items = _clean_agenda_items(payload.agenda_items)
    if "conclusions" in payload.model_fields_set:
        assembly.conclusions = payload.conclusions.strip() if payload.conclusions else None

    actor = _actor(request)
    assembly.updated_by = actor
    await assembly.save()
    await _sync_event_from_assembly(assembly, actor)
    assembly = await Assembly.get(id=assembly.id).select_related("event", "event__assigned_user")
    return _assembly_out(assembly)


@router.get("/{assembly_id}/summary.pdf")
async def download_assembly_summary(assembly_id: UUID, request: Request) -> Response:
    assembly = await Assembly.get_or_none(
        id=assembly_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).select_related("condominium")
    if not assembly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asamblea no encontrada")

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Para generar PDF instala la dependencia reportlab.",
        ) from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []
    logo_path = Path(__file__).resolve().parents[3] / "static" / "img" / "komite-logo.png"
    if logo_path.exists():
        story.append(Image(str(logo_path), width=4.6 * cm, height=2.5 * cm, hAlign="LEFT"))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Resumen de asamblea", styles["Title"]))
    story.append(Paragraph(assembly.title, styles["Heading2"]))
    story.append(Paragraph(f"Condominio: {assembly.condominium.name}", styles["Normal"]))
    story.append(Paragraph(f"Fecha: {assembly.scheduled_date.strftime('%d/%m/%Y')} {assembly.scheduled_start_time.strftime('%H:%M') if assembly.scheduled_start_time else ''}", styles["Normal"]))
    if assembly.location:
        story.append(Paragraph(f"Lugar: {assembly.location}", styles["Normal"]))
    story.append(Spacer(1, 0.35 * cm))

    agenda_rows = [["Punto", "Responsable", "Conclusión"]]
    for item in assembly.agenda_items or []:
        agenda_rows.append([
            item.get("title") or "",
            item.get("owner") or "",
            item.get("conclusion") or item.get("description") or "",
        ])
    if len(agenda_rows) == 1:
        agenda_rows.append(["Sin puntos registrados", "", ""])
    table = Table(agenda_rows, colWidths=[6 * cm, 4 * cm, 7 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102437")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbe3eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(Paragraph("Puntos tratados", styles["Heading2"]))
    story.append(table)
    story.append(Spacer(1, 0.35 * cm))

    attendee_rows = [["Asistente", "Rol", "Estado"]]
    for item in assembly.attendees or []:
        attendee_rows.append([item.get("name") or "", item.get("role") or "", item.get("attendance_status") or ""])
    if len(attendee_rows) == 1:
        attendee_rows.append(["Sin asistentes registrados", "", ""])
    attendees_table = Table(attendee_rows, colWidths=[8 * cm, 5 * cm, 4 * cm])
    attendees_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f7941d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbe3eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(Paragraph("Asistentes", styles["Heading2"]))
    story.append(attendees_table)
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Conclusiones", styles["Heading2"]))
    story.append(Paragraph(assembly.conclusions or "Sin conclusiones registradas.", styles["Normal"]))
    doc.build(story)
    buffer.seek(0)

    filename = f"asamblea-{assembly.scheduled_date.isoformat()}-{str(assembly.id)[:8]}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
