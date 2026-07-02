from __future__ import annotations

from app.core.settings import settings


class LocalWhisperService:
    _model = None

    def _load_model(self):
        if self.__class__._model is None:
            from faster_whisper import WhisperModel

            self.__class__._model = WhisperModel(
                settings.local_whisper_model,
                device=settings.local_whisper_device,
                compute_type=settings.local_whisper_compute_type,
            )
        return self.__class__._model

    def transcribe_audio(
        self,
        *,
        file_path: str,
        prompt: str | None = None,
        language: str | None = None,
    ) -> str:
        model = self._load_model()
        segments, _info = model.transcribe(
            file_path,
            language=language,
            initial_prompt=prompt,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments if segment.text).strip()

