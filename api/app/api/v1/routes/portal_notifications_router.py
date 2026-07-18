from __future__ import annotations

import re
import textwrap
from html import escape
from io import BytesIO
from pathlib import Path
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from tortoise.timezone import now

from app.core.auth.dependencies import require_access_token
from app.models.entities import OperationalNotification, Report, ReportVersion


router = APIRouter(
    prefix="/api/v1/portal/notifications",
    tags=["Portal operational notifications"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)

REVIEW_STATUSES = {"pending_review", "in_review"}
VISIBLE_STATUSES = {"pending_review", "in_review", "validated", "ready_to_send", "sent", "dismissed"}


class NotificationSummaryOut(BaseModel):
    pending_count: int
    in_review_count: int
    ready_to_send_count: int


class OperationalNotificationOut(BaseModel):
    id: UUID
    title: str
    summary: str | None = None
    body: str | None = None
    draft_body: str | None = None
    final_body: str | None = None
    status: str
    priority: str
    send_status: str
    send_channel: str
    event_id: UUID | None = None
    event_title: str | None = None
    external_service_order_id: UUID | None = None
    provider_name: str | None = None
    provider_email: str | None = None
    provider_phone: str | None = None
    report_id: UUID | None = None
    ai_request_id: UUID | None = None
    assigned_to_id: UUID | None = None
    validated_by_id: UUID | None = None
    validated_at: datetime | None = None
    mobile_payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class NotificationListOut(BaseModel):
    items: list[OperationalNotificationOut]


class NotificationUpdateRequest(BaseModel):
    final_body: str | None = None
    status: str | None = None


class NotificationValidateRequest(BaseModel):
    final_body: str = Field(..., min_length=3)
    title: str | None = Field(default=None, max_length=180)


def _actor(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return getattr(user, "email", None) or str(request.state.user_id)


def _out(notification: OperationalNotification) -> OperationalNotificationOut:
    order = getattr(notification, "external_service_order", None)
    event = getattr(notification, "event", None)
    return OperationalNotificationOut(
        id=notification.id,
        title=notification.title,
        summary=notification.summary,
        body=notification.body,
        draft_body=notification.draft_body,
        final_body=notification.final_body,
        status=notification.status,
        priority=notification.priority,
        send_status=notification.send_status,
        send_channel=notification.send_channel,
        event_id=notification.event_id,
        event_title=event.title if event else None,
        external_service_order_id=notification.external_service_order_id,
        provider_name=order.provider_name if order else (notification.metadata or {}).get("provider_name"),
        provider_email=order.provider_email if order else (notification.metadata or {}).get("provider_email"),
        provider_phone=order.provider_phone if order else (notification.metadata or {}).get("provider_phone"),
        report_id=notification.report_id,
        ai_request_id=notification.ai_request_id,
        assigned_to_id=notification.assigned_to_id,
        validated_by_id=notification.validated_by_id,
        validated_at=notification.validated_at,
        mobile_payload=notification.mobile_payload or {},
        metadata=notification.metadata or {},
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


def _pdf_inline(value: str) -> str:
    safe = escape(value or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)


def _pdf_blocks(markdown_text: str) -> list[dict]:
    blocks: list[dict] = []
    paragraph: list[str] = []
    current_list: dict | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph
        text = " ".join(item.strip() for item in paragraph if item.strip()).strip()
        if text:
            blocks.append({"type": "paragraph", "text": text})
        paragraph = []

    def flush_list() -> None:
        nonlocal current_list
        if current_list and current_list["items"]:
            blocks.append(current_list)
        current_list = None

    for raw_line in (markdown_text or "").replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            blocks.append({"type": "heading", "level": len(heading.group(1)), "text": heading.group(2).strip()})
            continue
        bold_heading = re.match(r"^\*\*(.+)\*\*:?$", line)
        if bold_heading:
            flush_paragraph()
            flush_list()
            blocks.append({"type": "heading", "level": 3, "text": bold_heading.group(1).strip()})
            continue
        unordered = re.match(r"^[-*]\s+(.+)$", line)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            flush_paragraph()
            ordered_list = bool(ordered)
            if not current_list or current_list["ordered"] != ordered_list:
                flush_list()
                current_list = {"type": "list", "ordered": ordered_list, "items": []}
            current_list["items"].append((ordered or unordered).group(1).strip())
            continue
        flush_list()
        paragraph.append(line)
    flush_paragraph()
    flush_list()
    return blocks


def _pdf_escape_text(value: str) -> bytes:
    text = (value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("cp1252", errors="replace")


def _basic_pdf_bytes(title: str, meta: list[tuple[str, str]], markdown_text: str) -> bytes:
    page_width = 595
    page_height = 842
    margin_x = 48
    start_y = 790
    line_height = 15
    lines: list[tuple[str, int, bool]] = [
        ("Informe de servicio - Proveedor externo", 10, True),
        (title, 16, True),
        ("", 10, False),
    ]
    for label, value in meta:
        lines.append((f"{label}: {value}", 10, False))
    lines.append(("", 10, False))

    for block in _pdf_blocks(markdown_text):
        if block["type"] == "heading":
            lines.append(("", 10, False))
            lines.append((str(block["text"]).replace("**", ""), 13, True))
            continue
        if block["type"] == "list":
            for index, item in enumerate(block["items"], start=1):
                prefix = f"{index}. " if block["ordered"] else "- "
                for wrapped_index, wrapped in enumerate(textwrap.wrap(str(item).replace("**", ""), width=92) or [""]):
                    lines.append(((prefix if wrapped_index == 0 else "  ") + wrapped, 10, False))
            lines.append(("", 10, False))
            continue
        for wrapped in textwrap.wrap(str(block["text"]).replace("**", ""), width=96) or [""]:
            lines.append((wrapped, 10, False))
        lines.append(("", 10, False))

    pages: list[list[tuple[str, int, bool]]] = []
    current: list[tuple[str, int, bool]] = []
    y = start_y
    for line in lines:
        size = line[1]
        needed = line_height + max(0, size - 10)
        if current and y - needed < 52:
            pages.append(current)
            current = []
            y = start_y
        current.append(line)
        y -= needed
    if current:
        pages.append(current)

    objects: list[bytes] = []
    pages_obj_id = 2
    font_regular_id = 3
    font_bold_id = 4
    page_ids: list[int] = []
    content_ids: list[int] = []
    next_id = 5
    for _ in pages:
        page_ids.append(next_id)
        content_ids.append(next_id + 1)
        next_id += 2

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = b" ".join(f"{page_id} 0 R".encode("ascii") for page_id in page_ids)
    objects.append(b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode("ascii") + b" >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    page_content_pairs: list[tuple[int, bytes, int]] = []
    for page_id, content_id, page_lines in zip(page_ids, content_ids, pages):
        commands = [b"BT"]
        y = start_y
        for text, size, bold in page_lines:
            font = b"/F2" if bold else b"/F1"
            commands.append(font + b" " + str(size).encode("ascii") + b" Tf")
            commands.append(f"{margin_x} {y} Td".encode("ascii"))
            commands.append(b"(" + _pdf_escape_text(text) + b") Tj")
            commands.append(f"{-margin_x} {-line_height - max(0, size - 10)} Td".encode("ascii"))
            y -= line_height + max(0, size - 10)
        commands.append(b"ET")
        stream = b"\n".join(commands)
        page_obj = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            + f"/Contents {content_id} 0 R >>".encode("ascii")
        )
        content_obj = b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        page_content_pairs.append((page_id, page_obj, content_id))
        page_content_pairs.append((content_id, content_obj, page_id))

    for object_id in range(5, next_id):
        for pair_id, obj, _ in page_content_pairs:
            if pair_id == object_id:
                objects.append(obj)
                break

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


async def _fetch_notification_relations(notification: OperationalNotification) -> OperationalNotification:
    await notification.fetch_related("condominium", "event", "external_service_order", "report")
    return notification


async def _notification_or_404(notification_id: UUID, request: Request) -> OperationalNotification:
    notification = await (
        OperationalNotification.filter(
            id=notification_id,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificacion no encontrada")
    return await _fetch_notification_relations(notification)


@router.get("/summary", response_model=NotificationSummaryOut)
async def get_notification_summary(request: Request) -> NotificationSummaryOut:
    base = OperationalNotification.filter(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    return NotificationSummaryOut(
        pending_count=await base.filter(status="pending_review").count(),
        in_review_count=await base.filter(status="in_review").count(),
        ready_to_send_count=await base.filter(status="ready_to_send").count(),
    )


@router.get("/", response_model=NotificationListOut)
async def list_notifications(request: Request, status_filter: str | None = None) -> NotificationListOut:
    query = OperationalNotification.filter(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if status_filter:
        statuses = [item.strip() for item in status_filter.split(",") if item.strip()]
        unknown = [item for item in statuses if item not in VISIBLE_STATUSES]
        if unknown:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de notificacion no valido")
        query = query.filter(status__in=statuses)
    items = await query.order_by("-created_at").limit(100)
    for item in items:
        await _fetch_notification_relations(item)
    return NotificationListOut(items=[_out(item) for item in items])


@router.get("/{notification_id}", response_model=OperationalNotificationOut)
async def get_notification(notification_id: UUID, request: Request) -> OperationalNotificationOut:
    return _out(await _notification_or_404(notification_id, request))


@router.patch("/{notification_id}", response_model=OperationalNotificationOut)
async def update_notification(
    notification_id: UUID,
    payload: NotificationUpdateRequest,
    request: Request,
) -> OperationalNotificationOut:
    notification = await _notification_or_404(notification_id, request)
    actor = _actor(request)
    if payload.final_body is not None:
        notification.final_body = payload.final_body.strip()
    if payload.status is not None:
        if payload.status not in {"pending_review", "in_review", "ready_to_send"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de notificacion no valido")
        if payload.status == "ready_to_send" and not (notification.final_body or payload.final_body or notification.draft_body):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes enviar un informe sin texto final")
        notification.status = payload.status
        notification.send_status = "pending" if payload.status == "ready_to_send" else "not_ready"
    elif notification.status == "pending_review":
        notification.status = "in_review"
    notification.updated_by = actor
    await notification.save()
    return _out(await _notification_or_404(notification_id, request))


@router.post("/{notification_id}/validate", response_model=OperationalNotificationOut)
async def validate_notification(
    notification_id: UUID,
    payload: NotificationValidateRequest,
    request: Request,
) -> OperationalNotificationOut:
    notification = await _notification_or_404(notification_id, request)
    actor = _actor(request)
    final_body = payload.final_body.strip()
    report_title = (payload.title or notification.title).strip()
    report_content = {
        "template": "external_service_report_review_v1",
        "title": report_title,
        "source": {
            "type": notification.source_type,
            "id": notification.source_id,
            "notification_id": str(notification.id),
            "external_service_order_id": str(notification.external_service_order_id) if notification.external_service_order_id else None,
            "event_id": str(notification.event_id) if notification.event_id else None,
        },
        "summary": notification.summary,
        "provider_submission": (notification.metadata or {}).get("submission", {}),
        "ai_draft": notification.draft_body,
        "final_text": final_body,
    }
    if notification.report_id:
        report = await Report.get(id=notification.report_id)
        report.title = report_title
        report.status = "validated"
        report.content = report_content
        report.approved_by_id = request.state.user_id
        report.approved_at = now()
        report.updated_by = actor
        await report.save()
        last_version = await ReportVersion.filter(report_id=report.id).order_by("-version_number").first()
        version_number = (last_version.version_number if last_version else 0) + 1
    else:
        report = await Report.create(
            company_id=notification.company_id,
            condominium_id=notification.condominium_id,
            operational_event_id=notification.event_id,
            operational_execution_id=notification.external_service_order.execution_id if notification.external_service_order else None,
            asset_id=notification.external_service_order.asset_id if notification.external_service_order else None,
            created_by_user_id=request.state.user_id,
            approved_by_id=request.state.user_id,
            report_type="service_report",
            title=report_title,
            status="validated",
            content=report_content,
            approved_at=now(),
            metadata={
                "source": "operational_notification",
                "operational_notification_id": str(notification.id),
                "external_service_order_id": str(notification.external_service_order_id) if notification.external_service_order_id else None,
            },
            created_by=actor,
            updated_by=actor,
        )
        version_number = 1

    await ReportVersion.create(
        company_id=notification.company_id,
        report_id=report.id,
        version_number=version_number,
        source="human",
        content=report_content,
        notes="Validado desde notificaciones operacionales.",
        created_by=actor,
        updated_by=actor,
    )

    notification.report_id = report.id
    notification.final_body = final_body
    notification.status = "ready_to_send"
    notification.send_status = "pending"
    notification.validated_by_id = request.state.user_id
    notification.validated_at = now()
    notification.mobile_payload = {
        "type": "service_report_ready",
        "title": report_title,
        "body": final_body,
        "report_id": str(report.id),
        "notification_id": str(notification.id),
        "condominium_id": str(notification.condominium_id),
        "event_id": str(notification.event_id) if notification.event_id else None,
    }
    notification.updated_by = actor
    await notification.save()
    if notification.external_service_order:
        notification.external_service_order.report_id = report.id
        notification.external_service_order.updated_by = actor
        await notification.external_service_order.save()
    return _out(await _notification_or_404(notification_id, request))


@router.post("/{notification_id}/dismiss", response_model=OperationalNotificationOut)
async def dismiss_notification(notification_id: UUID, request: Request) -> OperationalNotificationOut:
    notification = await _notification_or_404(notification_id, request)
    notification.status = "dismissed"
    notification.send_status = "not_ready"
    notification.updated_by = _actor(request)
    await notification.save()
    return _out(await _notification_or_404(notification_id, request))


@router.get("/{notification_id}/report.pdf")
async def download_notification_report_pdf(notification_id: UUID, request: Request) -> Response:
    notification = await _notification_or_404(notification_id, request)
    if notification.status not in {"ready_to_send", "validated", "sent"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El informe debe estar validado antes de descargarlo en PDF.",
        )

    reportlab_available = True
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        reportlab_available = False

    order = getattr(notification, "external_service_order", None)
    event = getattr(notification, "event", None)
    condominium = getattr(notification, "condominium", None)
    final_text = notification.final_body or notification.draft_body or notification.body or ""
    provider_name = order.provider_name if order else (notification.metadata or {}).get("provider_name") or "Sin proveedor"
    provider_contact = (order.provider_email or order.provider_phone) if order else (notification.metadata or {}).get("provider_email") or (notification.metadata or {}).get("provider_phone") or "Sin contacto"
    status_text = "Listo para enviar" if notification.status == "ready_to_send" else notification.status

    safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "-", notification.title.lower()).strip("-")[:80] or "informe"
    filename = f"{safe_title}-{str(notification.id)[:8]}.pdf"

    if not reportlab_available:
        pdf_bytes = _basic_pdf_bytes(
            notification.title,
            [
                ("Condominio", condominium.name if condominium else ""),
                ("Evento", event.title if event else ""),
                ("Proveedor", provider_name),
                ("Contacto", provider_contact),
                ("Fecha de recepcion", notification.created_at.strftime("%d/%m/%Y %H:%M")),
                ("Estado", status_text),
            ],
            final_text,
        )
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.7 * cm, leftMargin=1.7 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MetaLabel", parent=styles["Normal"], fontSize=7.5, textColor=colors.HexColor("#5b6778"), leading=10))
    styles.add(ParagraphStyle(name="MetaValue", parent=styles["Normal"], fontSize=9, leading=12, spaceBefore=2))
    styles.add(ParagraphStyle(name="DocSmallRight", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=8.5, textColor=colors.HexColor("#5b6778")))
    styles["Title"].textColor = colors.HexColor("#102437")
    styles["Heading2"].textColor = colors.HexColor("#102437")
    styles["Heading3"].textColor = colors.HexColor("#102437")
    styles["Normal"].leading = 13.5

    story = []
    logo_path = Path(__file__).resolve().parents[3] / "static" / "img" / "komite-logo.png"
    if logo_path.exists():
        logo = Image(str(logo_path))
        max_logo_width = 4.3 * cm
        max_logo_height = 2.8 * cm
        ratio = min(max_logo_width / logo.imageWidth, max_logo_height / logo.imageHeight)
        logo.drawWidth = logo.imageWidth * ratio
        logo.drawHeight = logo.imageHeight * ratio
        header = Table(
            [[logo, Paragraph("Informe de servicio<br/>Proveedor externo", styles["DocSmallRight"])]],
            colWidths=[8 * cm, 8 * cm],
        )
        header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(header)
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(_pdf_inline(notification.title), styles["Title"]))
    if condominium:
        story.append(Paragraph(f"Condominio: {_pdf_inline(condominium.name)}", styles["Normal"]))
    if event:
        story.append(Paragraph(f"Evento: {_pdf_inline(event.title)}", styles["Normal"]))
    story.append(Spacer(1, 0.35 * cm))

    meta_rows = [
        [
            Paragraph("Proveedor", styles["MetaLabel"]),
            Paragraph("Contacto", styles["MetaLabel"]),
            Paragraph("Fecha de recepcion", styles["MetaLabel"]),
            Paragraph("Estado", styles["MetaLabel"]),
        ],
        [
            Paragraph(_pdf_inline(provider_name), styles["MetaValue"]),
            Paragraph(_pdf_inline(provider_contact), styles["MetaValue"]),
            Paragraph(notification.created_at.strftime("%d/%m/%Y %H:%M"), styles["MetaValue"]),
            Paragraph(status_text, styles["MetaValue"]),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[4.2 * cm, 4.2 * cm, 4.2 * cm, 3.4 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbe3eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.45 * cm))

    for block in _pdf_blocks(final_text):
        if block["type"] == "heading":
            style = styles["Heading2"] if block["level"] <= 2 else styles["Heading3"]
            story.append(Paragraph(_pdf_inline(block["text"]), style))
            story.append(Spacer(1, 0.08 * cm))
        elif block["type"] == "list":
            items = [ListItem(Paragraph(_pdf_inline(item), styles["Normal"])) for item in block["items"]]
            story.append(ListFlowable(items, bulletType="1" if block["ordered"] else "bullet", leftIndent=18))
            story.append(Spacer(1, 0.18 * cm))
        else:
            story.append(Paragraph(_pdf_inline(block["text"]), styles["Normal"]))
            story.append(Spacer(1, 0.16 * cm))

    if not final_text.strip():
        story.append(Paragraph("Sin texto final.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
