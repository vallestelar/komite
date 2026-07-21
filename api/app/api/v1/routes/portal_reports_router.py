from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.core.auth.dependencies import require_access_token
from app.models.entities import Communication, Condominium, Report


router = APIRouter(
    prefix="/api/v1/portal/reports",
    tags=["Portal reports"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class ReportHistoryItem(BaseModel):
    id: str
    source: str
    source_label: str
    title: str
    status: str
    status_label: str
    category: str
    category_label: str
    issued_at: datetime | None = None
    created_at: datetime | None = None
    created_by_user_id: str | None = None
    format: str | None = None
    reference_id: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportHistoryResponse(BaseModel):
    items: list[ReportHistoryItem]
    meta: dict[str, int]
    summary: dict[str, int]


@router.get("/history", response_model=ReportHistoryResponse)
async def report_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> ReportHistoryResponse:
    condominium = await Condominium.get_or_none(id=request.state.condominium_id)
    company_id = condominium.company_id if condominium else request.state.company_id

    reports = await Report.filter(
        company_id=company_id,
        condominium_id=request.state.condominium_id,
    ).order_by("-created_at")
    communications = await Communication.filter(
        company_id=company_id,
        condominium_id=request.state.condominium_id,
    ).order_by("-created_at")

    items = [_report_item(report) for report in reports]
    items.extend(_communication_item(communication) for communication in communications)

    if q:
        needle = q.strip().lower()
        items = [
            item for item in items
            if needle in item.title.lower()
            or needle in item.category_label.lower()
            or needle in item.status_label.lower()
            or needle in (item.summary or "").lower()
        ]
    if source:
        items = [item for item in items if item.source == source]
    if status:
        items = [item for item in items if item.status == status]

    items.sort(key=_item_sort_key, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end]
    pages = max(1, (total + page_size - 1) // page_size)

    return ReportHistoryResponse(
        items=paged_items,
        meta={"total": total, "page": page, "page_size": page_size, "pages": pages},
        summary={
            "total": total,
            "reports": sum(1 for item in items if item.source == "report"),
            "certificates": sum(1 for item in items if item.category == "residence_certificate"),
            "communications": sum(1 for item in items if item.source == "communication"),
        },
    )


def _report_item(report: Report) -> ReportHistoryItem:
    metadata = report.metadata or {}
    content = report.content or {}
    category = report.report_type
    return ReportHistoryItem(
        id=str(report.id),
        source="report",
        source_label="Informe",
        title=report.title,
        status=report.status,
        status_label=_status_label(report.status),
        category=category,
        category_label=_report_type_label(category),
        issued_at=report.published_at or report.approved_at or report.created_at,
        created_at=report.created_at,
        created_by_user_id=str(report.created_by_user_id) if report.created_by_user_id else None,
        format=metadata.get("format"),
        reference_id=str(report.id),
        summary=_report_summary(report),
        metadata={
            "unit_identifier": metadata.get("unit_identifier"),
            "resident_name": metadata.get("resident_name"),
            "filename": metadata.get("filename"),
            "source": metadata.get("source"),
            "provider_name": metadata.get("provider_name") or (content.get("provider_submission") or {}).get("provider_name"),
        },
    )


def _item_sort_key(item: ReportHistoryItem) -> float:
    item_date = item.issued_at or item.created_at
    return item_date.timestamp() if item_date else 0


def _communication_item(communication: Communication) -> ReportHistoryItem:
    return ReportHistoryItem(
        id=str(communication.id),
        source="communication",
        source_label="Comunicado",
        title=communication.title,
        status=communication.status,
        status_label=_status_label(communication.status),
        category=communication.communication_type,
        category_label=_communication_type_label(communication.communication_type),
        issued_at=communication.sent_at or communication.scheduled_at or communication.created_at,
        created_at=communication.created_at,
        created_by_user_id=str(communication.created_by_user_id) if communication.created_by_user_id else None,
        format="comunicado",
        reference_id=str(communication.report_id) if communication.report_id else str(communication.id),
        summary=(communication.body or "")[:240],
        metadata={
            "audience": communication.audience,
            "channels": communication.channels or [],
        },
    )


def _report_summary(report: Report) -> str:
    content = report.content or {}
    metadata = report.metadata or {}
    if report.report_type == "residence_certificate":
        resident = metadata.get("resident_name") or content.get("resident_name") or "Residente"
        unit = metadata.get("unit_identifier") or content.get("unit_identifier") or "unidad"
        return f"Certificado emitido para {resident}, unidad {unit}."
    return str(content.get("summary") or content.get("final_text") or content.get("title") or "")[:240]


def _status_label(status: str) -> str:
    return {
        "draft": "Borrador",
        "validated": "Validado",
        "published": "Publicado",
        "issued": "Emitido",
        "sent": "Enviado",
        "scheduled": "Programado",
        "ready_to_send": "Listo para enviar",
    }.get(status, status.replace("_", " ").title())


def _report_type_label(report_type: str) -> str:
    return {
        "residence_certificate": "Certificado de residencia",
        "service_report": "Informe de proveedor",
        "maintenance": "Informe de mantención",
        "inspection": "Informe de inspección",
        "incident": "Informe de incidencia",
    }.get(report_type, report_type.replace("_", " ").title())


def _communication_type_label(communication_type: str) -> str:
    return {
        "notice": "Comunicado",
        "announcement": "Anuncio",
        "service_report": "Comunicado de proveedor",
        "incident": "Comunicado de incidencia",
    }.get(communication_type, communication_type.replace("_", " ").title())
