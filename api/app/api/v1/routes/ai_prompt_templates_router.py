from __future__ import annotations

import json
from io import BytesIO
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from app.api.v1.crud_router_factory import serialize_model
from app.core.auth.dependencies import require_komite_employee
from app.models.entities import AIPromptTemplate, Condominium
from app.schemas.entity_schemas import (
    AIPromptTemplateDuplicateToCondominiumOut,
    AIPromptTemplateDuplicateToCondominiumRequest,
    AIPromptTemplateOut,
)


router = APIRouter(
    prefix="/api/v1/ai-prompt-templates",
    tags=["AI prompt templates"],
    dependencies=[Depends(require_komite_employee())],
)


def _actor(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return getattr(user, "email", None) or getattr(request.state, "user_id", None) or "backoffice"


def _safe_filename(value: str) -> str:
    clean = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip().lower())
    return clean.strip("_") or "prompt_ia"


async def _get_template_or_404(template_id: UUID) -> AIPromptTemplate:
    template = await AIPromptTemplate.get_or_none(id=template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt IA no encontrado")
    return template


def _export_payload(template: AIPromptTemplate) -> dict:
    data = serialize_model(template)
    return {
        "kind": "komite_ai_prompt_template",
        "schema_version": 1,
        "template": data,
    }


@router.get("/{template_id}/export")
async def export_ai_prompt_template(template_id: UUID):
    template = await _get_template_or_404(template_id)
    payload = _export_payload(template)
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    buffer = BytesIO(content)
    filename = f"prompt_ia_{_safe_filename(template.key)}_v{template.version}.json"
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post(
    "/{template_id}/duplicate-to-condominium",
    response_model=AIPromptTemplateDuplicateToCondominiumOut,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_ai_prompt_template_to_condominium(
    template_id: UUID,
    payload: AIPromptTemplateDuplicateToCondominiumRequest,
    request: Request,
):
    base_template = await _get_template_or_404(template_id)
    condominium = await Condominium.get_or_none(id=payload.condominium_id)
    if not condominium:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condominio no encontrado")

    existing_versions = await AIPromptTemplate.filter(
        company_id=condominium.company_id,
        condominium_id=condominium.id,
        key=base_template.key,
    ).values_list("version", flat=True)
    next_version = max([base_template.version, *existing_versions], default=base_template.version) + 1 if existing_versions else base_template.version
    actor = _actor(request)
    template = await AIPromptTemplate.create(
        company_id=condominium.company_id,
        condominium_id=condominium.id,
        key=base_template.key,
        name=payload.name or f"{base_template.name} - {condominium.name}",
        description=base_template.description,
        purpose=base_template.purpose,
        module=base_template.module,
        asset_type=base_template.asset_type,
        system_template=base_template.system_template,
        user_template=base_template.user_template,
        required_variables=base_template.required_variables,
        optional_variables=base_template.optional_variables,
        default_model=base_template.default_model,
        default_temperature=base_template.default_temperature,
        default_max_tokens=base_template.default_max_tokens,
        reasoning_enabled=base_template.reasoning_enabled,
        expects_json=base_template.expects_json,
        version=next_version,
        status=payload.status,
        is_active=True,
        metadata={
            **(base_template.metadata or {}),
            "source_template_id": str(base_template.id),
            "source_template_name": base_template.name,
            "source_template_version": base_template.version,
            "duplicated_from_backoffice": True,
        },
        created_by=actor,
        updated_by=actor,
    )
    return AIPromptTemplateDuplicateToCondominiumOut(template=AIPromptTemplateOut(**serialize_model(template)))
