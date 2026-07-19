from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from tortoise.timezone import now

from app.core.auth.dependencies import require_access_token
from app.core.settings import settings
from app.models.entities import CondominiumAsset, ExternalServiceOrder, OperationalEventExecution, PlannedOperationalEvent
from app.services.llm_service import LLMService
from app.services.operational_notification_service import create_notification_from_external_order


portal_router = APIRouter(
    prefix="/api/v1/portal/operational-plan",
    tags=["Portal external service orders"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)

public_router = APIRouter(
    prefix="/api/v1/public/external-service-orders",
    tags=["Public external service orders"],
)


class ExternalServiceOrderCreateRequest(BaseModel):
    provider_name: str = Field(..., min_length=2, max_length=160)
    provider_email: EmailStr | None = None
    provider_phone: str | None = Field(default=None, max_length=40)
    title: str | None = Field(default=None, max_length=180)
    instructions: str | None = None
    prompt_key: str = Field(default="vendor_service_report", max_length=120)
    expires_in_days: int = Field(default=7, ge=1, le=60)
    public_base_url: str | None = None


class ExternalServiceOrderOut(BaseModel):
    id: UUID
    event_id: UUID
    title: str
    provider_name: str
    provider_email: str | None = None
    provider_phone: str | None = None
    status: str
    expires_at: datetime | None = None
    submitted_at: datetime | None = None
    prompt_key: str
    public_url: str | None = None


class PublicExternalServiceOrderOut(BaseModel):
    token_status: str
    id: UUID
    title: str
    instructions: str | None = None
    provider_name: str
    condominium_name: str
    condominium_address: str | None = None
    event_title: str
    event_description: str | None = None
    planned_date: str
    asset_name: str | None = None
    status: str
    expires_at: datetime | None = None


class ExternalServiceSubmissionRequest(BaseModel):
    submitted_by_name: str = Field(..., min_length=2, max_length=160)
    submitted_by_email: EmailStr | None = None
    execution_date: str | None = None
    result: str = Field(default="completed", max_length=60)
    work_performed: str = Field(..., min_length=3)
    findings: str | None = None
    materials_used: str | None = None
    recommendations: str | None = None
    next_visit_required: bool = False
    additional_comments: str | None = None


class ExternalServiceSubmissionOut(BaseModel):
    id: UUID
    status: str
    execution_id: UUID | None = None
    ai_request_id: UUID | None = None
    ai_generated_text: str | None = None
    ai_error: str | None = None


def _hash_token(token: str) -> str:
    secret = settings.jwt_secret_key or "komite"
    return hashlib.sha256(f"{token}:{secret}".encode("utf-8")).hexdigest()


def _public_url(base_url: str | None, token: str) -> str:
    path = f"/service-order/{token}"
    return f"{base_url.rstrip('/')}{path}" if base_url else path


def _order_out(order: ExternalServiceOrder) -> ExternalServiceOrderOut:
    return ExternalServiceOrderOut(
        id=order.id,
        event_id=order.event_id,
        title=order.title,
        provider_name=order.provider_name,
        provider_email=order.provider_email,
        provider_phone=order.provider_phone,
        status=order.status,
        expires_at=order.expires_at,
        submitted_at=order.submitted_at,
        prompt_key=order.prompt_key,
        public_url=order.public_url,
    )


async def _event_or_404(event_id: UUID, request: Request) -> PlannedOperationalEvent:
    event = await PlannedOperationalEvent.get_or_none(
        id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).select_related("condominium")
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return event


async def _asset_for_event(event: PlannedOperationalEvent) -> CondominiumAsset | None:
    metadata = event.metadata or {}
    asset_id = metadata.get("asset_id")
    if asset_id:
        try:
            return await CondominiumAsset.get_or_none(id=UUID(str(asset_id)), condominium_id=event.condominium_id)
        except (TypeError, ValueError):
            return None
    asset_name = metadata.get("asset_name")
    if asset_name:
        return await CondominiumAsset.get_or_none(condominium_id=event.condominium_id, name=asset_name)
    return None


async def _order_by_token(token: str) -> ExternalServiceOrder:
    order = await (
        ExternalServiceOrder.get_or_none(token_hash=_hash_token(token))
        .select_related("event", "condominium", "asset")
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    if order.expires_at and order.expires_at < now():
        order.status = "expired"
        await order.save()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="El link expiro")
    return order


@portal_router.get("/events/{event_id}/external-service-orders", response_model=list[ExternalServiceOrderOut])
async def list_event_external_service_orders(event_id: UUID, request: Request) -> list[ExternalServiceOrderOut]:
    await _event_or_404(event_id, request)
    orders = await ExternalServiceOrder.filter(
        event_id=event_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).order_by("-created_at")
    return [_order_out(order) for order in orders]


@portal_router.post("/events/{event_id}/external-service-orders", response_model=ExternalServiceOrderOut, status_code=status.HTTP_201_CREATED)
async def create_event_external_service_order(
    event_id: UUID,
    payload: ExternalServiceOrderCreateRequest,
    request: Request,
) -> ExternalServiceOrderOut:
    event = await _event_or_404(event_id, request)
    asset = await _asset_for_event(event)
    token = secrets.token_urlsafe(32)
    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    order = await ExternalServiceOrder.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        event_id=event.id,
        asset_id=asset.id if asset else None,
        token_hash=_hash_token(token),
        title=(payload.title or event.title).strip(),
        instructions=payload.instructions.strip() if payload.instructions else event.description,
        provider_name=payload.provider_name.strip(),
        provider_email=str(payload.provider_email) if payload.provider_email else None,
        provider_phone=payload.provider_phone.strip() if payload.provider_phone else None,
        prompt_key=payload.prompt_key,
        status="pending",
        expires_at=now() + timedelta(days=payload.expires_in_days),
        public_url=_public_url(payload.public_base_url, token),
        metadata={
            "created_from": "portal_operational_plan",
            "event_title": event.title,
            "asset_name": asset.name if asset else (event.metadata or {}).get("asset_name"),
        },
        created_by=actor,
        updated_by=actor,
    )
    return _order_out(order)


@public_router.get("/{token}", response_model=PublicExternalServiceOrderOut)
async def get_public_external_service_order(token: str) -> PublicExternalServiceOrderOut:
    order = await _order_by_token(token)
    return PublicExternalServiceOrderOut(
        token_status="valid",
        id=order.id,
        title=order.title,
        instructions=order.instructions,
        provider_name=order.provider_name,
        condominium_name=order.condominium.name,
        condominium_address=order.condominium.address,
        event_title=order.event.title,
        event_description=order.event.description,
        planned_date=order.event.planned_date.isoformat(),
        asset_name=order.asset.name if order.asset else (order.metadata or {}).get("asset_name"),
        status=order.status,
        expires_at=order.expires_at,
    )


@public_router.post("/{token}/submit", response_model=ExternalServiceSubmissionOut)
async def submit_public_external_service_order(
    token: str,
    payload: ExternalServiceSubmissionRequest,
) -> ExternalServiceSubmissionOut:
    order = await _order_by_token(token)
    if order.status in {"submitted", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La orden ya fue enviada")

    submission = payload.model_dump()
    actor = f"external:{payload.submitted_by_email or payload.submitted_by_name}"
    execution = await OperationalEventExecution.create(
        company_id=order.company_id,
        event_id=order.event_id,
        executed_at=now(),
        result=payload.result,
        comments=payload.work_performed,
        requires_follow_up=payload.next_visit_required,
        metadata={
            "source": "external_service_order",
            "external_service_order_id": str(order.id),
            "submission": submission,
        },
        created_by=actor,
        updated_by=actor,
    )

    order.execution_id = execution.id
    order.status = "submitted"
    order.submitted_at = now()
    order.submission_payload = submission

    event = await PlannedOperationalEvent.get(id=order.event_id).select_related("condominium")
    event.status = "completed" if payload.result in {"completed", "conforme", "resolved"} else "in_progress"
    event.updated_by = actor
    await event.save()

    ai_error = None
    execution_date = payload.execution_date or now().date().isoformat()
    try:
        execution_date = datetime.fromisoformat(execution_date).strftime("%d/%m/%Y")
    except ValueError:
        pass
    try:
        completion = await LLMService().complete_prompt(
            prompt_key=order.prompt_key,
            variables={
                "condominium_name": order.condominium.name,
                "event_title": event.title,
                "asset_name": order.asset.name if order.asset else (order.metadata or {}).get("asset_name"),
                "provider_name": order.provider_name,
                "submitted_by_name": payload.submitted_by_name,
                "execution_date": execution_date,
                "result": payload.result,
                "instructions": order.instructions,
                "work_performed": payload.work_performed,
                "findings": payload.findings,
                "materials_used": payload.materials_used,
                "recommendations": payload.recommendations,
                "next_visit_required": "Si" if payload.next_visit_required else "No",
                "additional_comments": payload.additional_comments,
                "inspection_type": event.title,
                "general_status": payload.result,
                "doors_status": "",
                "cabin_status": "",
                "controls_status": "",
                "machine_room_status": "",
                "pit_status": "",
                "noise_or_vibration": "",
                "actions_performed": payload.work_performed,
                "evidence_summary": "Formulario publico enviado por proveedor externo.",
                "asset_history": "",
            },
            company_id=order.company_id,
            condominium_id=order.condominium_id,
            metadata={
                "source": "external_service_order",
                "external_service_order_id": str(order.id),
            },
        )
        order.ai_request_id = completion.ai_request_id
        order.ai_generated_text = completion.text
    except Exception as exc:
        ai_error = str(exc)
        metadata = dict(order.metadata or {})
        metadata["ai_error"] = ai_error
        order.metadata = metadata

    await order.save()
    await create_notification_from_external_order(
        order=order,
        event=event,
        submission=submission,
        ai_error=ai_error,
        actor=actor,
    )
    return ExternalServiceSubmissionOut(
        id=order.id,
        status=order.status,
        execution_id=execution.id,
        ai_request_id=order.ai_request_id,
        ai_generated_text=order.ai_generated_text,
        ai_error=ai_error,
    )
