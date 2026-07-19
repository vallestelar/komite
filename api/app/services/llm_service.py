from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from openai import OpenAI

from app.core.settings import settings
from app.models.entities import AIPromptTemplate, AIRequest
from app.services.prompt_catalog import PromptTemplate, get_prompt_template, render_prompt


VENDOR_SERVICE_REPORT_GUARDRAILS = (
    "\n\nReglas obligatorias para informes de proveedor externo:\n"
    "- Usa fechas en formato DD/MM/AAAA.\n"
    "- No incluyas separadores Markdown como --- o --.\n"
    "- No incluyas firma, 'Elaborado por', 'Eres Komite' ni 'Estado del informe'.\n"
    "- Si no recibes numero de orden, omite esa linea; no escribas [Pendiente].\n"
    "- Redacta solo el contenido del informe que vera el supervisor y el destinatario final."
)


@dataclass
class LLMCompletion:
    ai_request_id: UUID
    provider: str
    model: str
    purpose: str
    text: str
    raw: dict[str, Any]
    tokens_input: int | None = None
    tokens_output: int | None = None


class LLMService:
    def provider(self) -> str:
        return (settings.ai_provider or "deepseek").strip().lower()

    def default_model(self, *, reasoning: bool = False) -> str:
        provider = self.provider()
        if provider == "deepseek":
            if reasoning:
                return settings.deepseek_reasoning_model
            return settings.deepseek_model or settings.ai_model or "deepseek-v4-flash"
        return settings.ai_model or "gpt-4o-mini"

    def is_configured(self) -> bool:
        try:
            self._api_key()
            return True
        except RuntimeError:
            return False

    def _api_key(self) -> str:
        provider = self.provider()
        if provider == "deepseek":
            value = self._clean_secret(settings.deepseek_api_key) or self._clean_secret(settings.ai_api_key)
            if value and value != "change_me":
                return value
            raise RuntimeError("DeepSeek no esta configurado. Define DEEPSEEK_API_KEY o AI_API_KEY.")

        value = self._clean_secret(settings.ai_api_key)
        if value and value != "change_me":
            return value
        raise RuntimeError(f"Proveedor IA no configurado: {provider}. Define AI_API_KEY.")

    def _base_url(self) -> str | None:
        provider = self.provider()
        if provider == "deepseek":
            return settings.ai_base_url or settings.deepseek_base_url or "https://api.deepseek.com"
        return settings.ai_base_url

    def _client(self) -> OpenAI:
        base_url = self._base_url()
        kwargs: dict[str, Any] = {"api_key": self._api_key()}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    async def complete_prompt(
        self,
        *,
        prompt_key: str,
        variables: dict[str, Any],
        company_id: UUID | str | None = None,
        condominium_id: UUID | str | None = None,
        requested_by_id: UUID | str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        reasoning: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> LLMCompletion:
        template = await self._prompt_template(prompt_key, company_id=company_id, condominium_id=condominium_id)
        messages = render_prompt(template, variables)
        return await self.complete_messages(
            messages=messages,
            purpose=template.purpose,
            company_id=company_id,
            condominium_id=condominium_id,
            requested_by_id=requested_by_id,
            model=model or template.metadata.get("default_model"),
            temperature=temperature if temperature is not None else template.default_temperature,
            max_tokens=max_tokens or template.default_max_tokens,
            reasoning=reasoning or bool(template.metadata.get("reasoning_enabled")),
            metadata={
                **(metadata or {}),
                "prompt_key": prompt_key,
                "template_source": template.metadata.get("source", "code"),
                "expects_json": template.expects_json,
                "variables": variables,
            },
        )

    async def _prompt_template(
        self,
        key: str,
        *,
        company_id: UUID | str | None,
        condominium_id: UUID | str | None,
    ) -> PromptTemplate:
        saved_template = None
        base_filter = {"key": key, "is_active": True, "status__in": ["active", "published"]}
        if condominium_id:
            saved_template = await AIPromptTemplate.filter(
                **base_filter,
                condominium_id=condominium_id,
            ).order_by("-version", "-updated_at").first()
        if not saved_template and company_id:
            saved_template = await AIPromptTemplate.filter(
                **base_filter,
                company_id=company_id,
                condominium_id__isnull=True,
            ).order_by("-version", "-updated_at").first()
        if not saved_template:
            saved_template = await AIPromptTemplate.filter(
                **base_filter,
                company_id__isnull=True,
                condominium_id__isnull=True,
            ).order_by("-version", "-updated_at").first()

        if saved_template:
            system_template = saved_template.system_template
            user_template = saved_template.user_template
            if saved_template.key == "vendor_service_report":
                system_template = system_template.replace("Eres Komite", "Actuas como asistente operativo de Komite")
                user_template = f"{user_template.rstrip()}{VENDOR_SERVICE_REPORT_GUARDRAILS}"
            return PromptTemplate(
                key=saved_template.key,
                name=saved_template.name,
                purpose=saved_template.purpose,
                system_template=system_template,
                user_template=user_template,
                required_variables=tuple(saved_template.required_variables or []),
                optional_variables=tuple(saved_template.optional_variables or []),
                default_temperature=saved_template.default_temperature,
                default_max_tokens=saved_template.default_max_tokens,
                expects_json=saved_template.expects_json,
                metadata={
                    **(saved_template.metadata or {}),
                    "source": "database",
                    "template_id": str(saved_template.id),
                    "module": saved_template.module,
                    "asset_type": saved_template.asset_type,
                    "version": saved_template.version,
                    "default_model": saved_template.default_model,
                    "reasoning_enabled": saved_template.reasoning_enabled,
                },
            )

        return get_prompt_template(key)

    async def complete_messages(
        self,
        *,
        messages: list[dict[str, str]],
        purpose: str,
        company_id: UUID | str | None = None,
        condominium_id: UUID | str | None = None,
        requested_by_id: UUID | str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        reasoning: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> LLMCompletion:
        provider = self.provider()
        selected_model = model or self.default_model(reasoning=reasoning)
        selected_temperature = settings.ai_temperature if temperature is None else temperature
        selected_max_tokens = max_tokens or settings.ai_max_tokens

        ai_request = await AIRequest.create(
            company_id=company_id,
            condominium_id=condominium_id,
            requested_by_id=requested_by_id,
            provider=provider,
            model=selected_model,
            purpose=purpose,
            status="pending",
            input_payload={
                "messages": messages,
                "temperature": selected_temperature,
                "max_tokens": selected_max_tokens,
                "reasoning": reasoning,
            },
            metadata=metadata or {},
        )

        try:
            response = self._client().chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=selected_temperature,
                max_tokens=selected_max_tokens,
                stream=False,
                **self._provider_extra_kwargs(reasoning=reasoning),
            )
            choice = response.choices[0] if response.choices else None
            text = choice.message.content if choice and choice.message else ""
            usage = getattr(response, "usage", None)
            tokens_input = getattr(usage, "prompt_tokens", None) if usage else None
            tokens_output = getattr(usage, "completion_tokens", None) if usage else None
            raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else {}

            ai_request.status = "completed"
            ai_request.output_payload = {"text": text, "raw": raw}
            ai_request.tokens_input = tokens_input
            ai_request.tokens_output = tokens_output
            await ai_request.save()

            return LLMCompletion(
                ai_request_id=ai_request.id,
                provider=provider,
                model=selected_model,
                purpose=purpose,
                text=text,
                raw=raw,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
            )
        except Exception as exc:
            ai_request.status = "failed"
            ai_request.error_message = str(exc)
            await ai_request.save()
            raise

    def _provider_extra_kwargs(self, *, reasoning: bool) -> dict[str, Any]:
        if self.provider() == "deepseek" and reasoning:
            return {
                "reasoning_effort": "high",
                "extra_body": {"thinking": {"type": "enabled"}},
            }
        return {}

    @staticmethod
    def _clean_secret(value: str | None) -> str | None:
        if not value:
            return None
        clean = value.strip()
        lowered = clean.lower()
        placeholders = {
            "change_me",
            "tu_deepseek_api_key",
            "your_deepseek_api_key",
            "your_api_key",
            "api_key",
        }
        if not clean or lowered in placeholders or lowered.startswith("tu_"):
            return None
        return clean
