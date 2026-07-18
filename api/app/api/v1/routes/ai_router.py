from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth.dependencies import require_access_token
from app.models.entities import AIPromptTemplate
from app.schemas.ai_schema import AIChatRequest, AICompletionResponse, AIPromptRequest, PromptTemplateOut
from app.services.llm_service import LLMService
from app.services.prompt_catalog import list_prompt_templates


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"],
    dependencies=[Depends(require_access_token())],
)


@router.get("/prompts", response_model=list[PromptTemplateOut])
async def list_prompts() -> list[PromptTemplateOut]:
    code_prompts = [
        PromptTemplateOut(
            key=item.key,
            name=item.name,
            purpose=item.purpose,
            required_variables=list(item.required_variables),
            optional_variables=list(item.optional_variables),
            default_temperature=item.default_temperature,
            default_max_tokens=item.default_max_tokens,
            expects_json=item.expects_json,
            metadata=item.metadata,
        )
        for item in list_prompt_templates()
    ]
    saved_prompts = await AIPromptTemplate.filter(is_active=True, status__in=["active", "published"]).order_by("key", "-version")
    merged = {item.key: item for item in code_prompts}
    for item in saved_prompts:
        merged[item.key] = PromptTemplateOut(
            key=item.key,
            name=item.name,
            purpose=item.purpose,
            required_variables=list(item.required_variables or []),
            optional_variables=list(item.optional_variables or []),
            default_temperature=item.default_temperature,
            default_max_tokens=item.default_max_tokens,
            expects_json=item.expects_json,
            metadata={
                **(item.metadata or {}),
                "source": "database",
                "template_id": str(item.id),
                "module": item.module,
                "asset_type": item.asset_type,
                "version": item.version,
                "status": item.status,
            },
        )
    return sorted(merged.values(), key=lambda item: item.key)


@router.post("/prompts/run", response_model=AICompletionResponse)
async def run_prompt(payload: AIPromptRequest, request: Request) -> AICompletionResponse:
    service = LLMService()
    try:
        completion = await service.complete_prompt(
            prompt_key=payload.prompt_key,
            variables=payload.variables,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
            requested_by_id=request.state.user_id,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            reasoning=payload.reasoning,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return AICompletionResponse(**completion.__dict__)


@router.post("/chat", response_model=AICompletionResponse)
async def run_chat(payload: AIChatRequest, request: Request) -> AICompletionResponse:
    service = LLMService()
    try:
        completion = await service.complete_messages(
            messages=[item.model_dump() for item in payload.messages],
            purpose=payload.purpose,
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
            requested_by_id=request.state.user_id,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            reasoning=payload.reasoning,
            metadata=payload.metadata,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return AICompletionResponse(**completion.__dict__)
