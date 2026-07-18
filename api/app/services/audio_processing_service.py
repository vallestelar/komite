from __future__ import annotations

from uuid import UUID

from fastapi import UploadFile

from app.core.settings import settings
from app.models.entities import AIRequest, Attachment, Condominium, Incident, Inspection, Task
from app.schemas.audio_schema import AudioProcessingResponse
from app.services.file_storage_service import FileStorageService
from app.services.llm_service import LLMService
from app.services.local_whisper_service import LocalWhisperService
from app.services.openai_service import OpenAIService


DEFAULT_TRANSCRIPTION_PROMPT = (
    "Audio de terreno de una administradora de condominios en Chile. "
    "Puede incluir nombres de condominios, torres, bombas, ascensores, portones, "
    "filtraciones, conserjeria, comite y mantenciones. Transcribe sin inventar."
)

DEFAULT_DRAFT_PROMPT = (
    "Eres Komite, un asistente operativo para administracion de condominios. "
    "Convierte la transcripcion en un texto profesional y verificable. "
    "No inventes hechos. Separa hechos, observaciones, recomendaciones y proximos pasos. "
    "Si falta informacion, indicalo como pendiente de validacion."
)


class AudioProcessingService:
    def __init__(self):
        self.storage = FileStorageService()
        self.llm = LLMService()
        self.openai = OpenAIService()
        self.local_whisper = LocalWhisperService()

    def _transcription_provider(self) -> str:
        return (settings.transcription_provider or "local_whisper").lower()

    def _transcription_model(self) -> str:
        if self._transcription_provider() == "local_whisper":
            return settings.local_whisper_model
        return settings.openai_transcription_model

    def _transcribe(self, *, file_path: str, prompt: str | None, language: str | None) -> str:
        provider = self._transcription_provider()
        if provider == "local_whisper":
            return self.local_whisper.transcribe_audio(
                file_path=file_path,
                prompt=prompt,
                language=language,
            )
        if provider == "openai":
            return self.openai.transcribe_audio(
                file_path=file_path,
                prompt=prompt,
                language=language,
            )
        raise ValueError(f"Proveedor de transcripcion no soportado: {provider}")

    async def _resolve_company_id(
        self,
        *,
        condominium_id: UUID | None,
        incident_id: UUID | None,
        task_id: UUID | None,
        inspection_id: UUID | None,
    ) -> UUID | None:
        if condominium_id:
            condominium = await Condominium.get_or_none(id=condominium_id)
            return condominium.company_id if condominium else None

        if incident_id:
            incident = await Incident.get_or_none(id=incident_id)
            return incident.company_id if incident else None

        if task_id:
            task = await Task.get_or_none(id=task_id)
            return task.company_id if task else None

        if inspection_id:
            inspection = await Inspection.get_or_none(id=inspection_id)
            return inspection.company_id if inspection else None

        return None

    async def process_audio(
        self,
        *,
        upload: UploadFile,
        user_id: str | None,
        condominium_id: UUID | None = None,
        incident_id: UUID | None = None,
        task_id: UUID | None = None,
        inspection_id: UUID | None = None,
        language: str | None = None,
        transcription_prompt: str | None = None,
        draft_prompt: str | None = None,
        generate_draft: bool = True,
    ) -> AudioProcessingResponse:
        stored = await self.storage.save_audio(upload)
        company_id = await self._resolve_company_id(
            condominium_id=condominium_id,
            incident_id=incident_id,
            task_id=task_id,
            inspection_id=inspection_id,
        )

        attachment = await Attachment.create(
            company_id=company_id,
            condominium_id=condominium_id,
            uploaded_by_id=user_id,
            incident_id=incident_id,
            task_id=task_id,
            inspection_id=inspection_id,
            file_name=stored.file_name,
            file_path=stored.file_path,
            file_type=stored.file_type,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            checksum=stored.checksum,
        )

        transcription_request = await AIRequest.create(
            company_id=company_id,
            condominium_id=condominium_id,
            requested_by_id=user_id,
            provider=self._transcription_provider(),
            model=self._transcription_model(),
            purpose="audio_transcription",
            status="pending",
            input_payload={
                "attachment_id": str(attachment.id),
                "file_name": stored.file_name,
                "language": language,
                "prompt": transcription_prompt or DEFAULT_TRANSCRIPTION_PROMPT,
            },
        )

        try:
            transcript = self._transcribe(
                file_path=stored.file_path,
                prompt=transcription_prompt or DEFAULT_TRANSCRIPTION_PROMPT,
                language=language,
            )
            transcription_request.status = "completed"
            transcription_request.output_payload = {"text": transcript}
            await transcription_request.save()
        except Exception as exc:
            transcription_request.status = "failed"
            transcription_request.error_message = str(exc)
            await transcription_request.save()
            return AudioProcessingResponse(
                attachment_id=attachment.id,
                file_name=stored.file_name,
                file_type=stored.file_type,
                mime_type=stored.mime_type,
                size_bytes=stored.size_bytes,
                transcription_ai_request_id=transcription_request.id,
                provider=self._transcription_provider(),
                transcription_model=self._transcription_model(),
                draft_model=settings.openai_draft_model,
                status="failed",
                error_message=str(exc),
            )

        draft_text = None
        draft_ai_request_id = None
        draft_error_message = None

        if generate_draft:
            prompt = draft_prompt or DEFAULT_DRAFT_PROMPT
            try:
                completion = await self.llm.complete_prompt(
                    prompt_key="generic_assistant",
                    variables={"prompt": f"{prompt}\n\nTranscripcion:\n{transcript}"},
                    company_id=company_id,
                    condominium_id=condominium_id,
                    requested_by_id=user_id,
                    metadata={
                        "source": "audio_processing_service",
                        "attachment_id": str(attachment.id),
                        "transcription_ai_request_id": str(transcription_request.id),
                    },
                )
                draft_text = completion.text
                draft_ai_request_id = completion.ai_request_id
            except Exception as exc:
                draft_error_message = str(exc)

        return AudioProcessingResponse(
            attachment_id=attachment.id,
            file_name=stored.file_name,
            file_type=stored.file_type,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            transcription_text=transcript,
            draft_text=draft_text,
            transcription_ai_request_id=transcription_request.id,
            draft_ai_request_id=draft_ai_request_id,
            provider=self._transcription_provider(),
            transcription_model=self._transcription_model(),
            draft_model=self.llm.default_model() if generate_draft else None,
            status="completed" if not generate_draft or draft_error_message is None else "partial",
            error_message=draft_error_message,
        )
