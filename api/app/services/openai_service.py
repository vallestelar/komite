from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from app.core.settings import settings


class OpenAIService:
    def __init__(self):
        self.provider = settings.ai_provider or "openai"

    @property
    def is_configured(self) -> bool:
        return self.provider == "openai" and bool(settings.ai_api_key and settings.ai_api_key != "change_me")

    def _client(self) -> OpenAI:
        if not self.is_configured:
            raise RuntimeError("OpenAI no esta configurado. Define AI_PROVIDER=openai y AI_API_KEY.")
        return OpenAI(api_key=settings.ai_api_key)

    def transcribe_audio(
        self,
        *,
        file_path: str,
        prompt: str | None = None,
        language: str | None = None,
    ) -> str:
        client = self._client()
        kwargs = {
            "model": settings.openai_transcription_model,
            "response_format": "text",
        }

        if prompt:
            kwargs["prompt"] = prompt
        if language:
            kwargs["language"] = language

        with Path(file_path).open("rb") as audio_file:
            kwargs["file"] = audio_file
            result = client.audio.transcriptions.create(**kwargs)

        return result if isinstance(result, str) else getattr(result, "text", str(result))

    def generate_draft_from_transcript(
        self,
        *,
        transcript: str,
        prompt: str,
    ) -> str:
        client = self._client()
        response = client.responses.create(
            model=settings.openai_draft_model or settings.ai_model,
            instructions=prompt,
            input=transcript,
        )
        return response.output_text
