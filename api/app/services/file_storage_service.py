from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.settings import settings


@dataclass
class StoredFile:
    file_name: str
    file_path: str
    file_type: str
    mime_type: str | None
    size_bytes: int
    checksum: str


class FileStorageService:
    AUDIO_EXTENSIONS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg", ".oga"}

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir)

    def _safe_name(self, file_name: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_name).strip("._")
        return clean or "audio"

    def _audio_dir(self) -> Path:
        target = self.base_dir / "audio"
        target.mkdir(parents=True, exist_ok=True)
        return target

    async def save_audio(self, upload: UploadFile) -> StoredFile:
        original_name = self._safe_name(upload.filename or "audio")
        suffix = Path(original_name).suffix.lower()
        if suffix not in self.AUDIO_EXTENSIONS:
            raise ValueError(f"Formato de audio no permitido: {suffix or 'sin extension'}")

        max_bytes = settings.max_audio_upload_mb * 1024 * 1024
        target_name = f"{uuid4()}_{original_name}"
        target_path = self._audio_dir() / target_name

        checksum = hashlib.sha256()
        size = 0

        with target_path.open("wb") as file:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break

                size += len(chunk)
                if size > max_bytes:
                    file.close()
                    target_path.unlink(missing_ok=True)
                    raise ValueError(f"El audio supera el limite de {settings.max_audio_upload_mb} MB")

                checksum.update(chunk)
                file.write(chunk)

        await upload.seek(0)

        return StoredFile(
            file_name=original_name,
            file_path=str(target_path),
            file_type="audio",
            mime_type=upload.content_type,
            size_bytes=size,
            checksum=checksum.hexdigest(),
        )

