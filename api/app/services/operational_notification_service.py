from __future__ import annotations

from typing import Any

from app.models.entities import ExternalServiceOrder, OperationalNotification, PlannedOperationalEvent


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_provider_submission_text(order: ExternalServiceOrder, submission: dict[str, Any], ai_error: str | None = None) -> str:
    lines = [
        f"Proveedor: {_clean(order.provider_name)}",
        f"Responsable que informa: {_clean(submission.get('submitted_by_name'))}",
        f"Resultado declarado: {_clean(submission.get('result')) or 'Sin resultado informado'}",
        "",
        "Trabajo realizado:",
        _clean(submission.get("work_performed")) or "Sin detalle informado.",
    ]
    optional_sections = [
        ("Hallazgos", submission.get("findings")),
        ("Materiales o repuestos", submission.get("materials_used")),
        ("Recomendaciones", submission.get("recommendations")),
        ("Comentarios adicionales", submission.get("additional_comments")),
    ]
    for label, value in optional_sections:
        if _clean(value):
            lines.extend(["", f"{label}:", _clean(value)])
    if submission.get("next_visit_required"):
        lines.extend(["", "Proxima visita requerida: Si"])
    if ai_error:
        lines.extend(["", "Nota interna:", "La IA no pudo generar el borrador. Se deja el texto del proveedor para revision."])
    return "\n".join(lines)


async def create_notification_from_external_order(
    order: ExternalServiceOrder,
    event: PlannedOperationalEvent,
    submission: dict[str, Any],
    ai_error: str | None,
    actor: str,
) -> OperationalNotification:
    existing = await OperationalNotification.get_or_none(external_service_order_id=order.id)
    draft_body = order.ai_generated_text or build_provider_submission_text(order, submission, ai_error)
    summary = _clean(submission.get("work_performed"))
    if len(summary) > 240:
        summary = f"{summary[:237]}..."
    metadata = {
        "provider_name": order.provider_name,
        "provider_email": order.provider_email,
        "provider_phone": order.provider_phone,
        "submitted_by_name": submission.get("submitted_by_name"),
        "submitted_by_email": submission.get("submitted_by_email"),
        "result": submission.get("result"),
        "next_visit_required": submission.get("next_visit_required"),
        "ai_error": ai_error,
        "submission": submission,
    }
    values = {
        "company_id": order.company_id,
        "condominium_id": order.condominium_id,
        "event_id": event.id,
        "external_service_order_id": order.id,
        "ai_request_id": order.ai_request_id,
        "source_type": "external_service_order",
        "source_id": str(order.id),
        "title": f"Informe proveedor: {order.title}",
        "summary": summary or f"Entrega recibida de {order.provider_name}",
        "body": build_provider_submission_text(order, submission, ai_error),
        "draft_body": draft_body,
        "final_body": draft_body,
        "status": "pending_review",
        "priority": event.priority or "medium",
        "assigned_to_id": event.assigned_user_id,
        "send_status": "not_ready",
        "send_channel": "mobile_app",
        "metadata": metadata,
        "updated_by": actor,
    }
    if existing:
        for field, value in values.items():
            setattr(existing, field, value)
        await existing.save()
        return existing
    return await OperationalNotification.create(**values, created_by=actor)
