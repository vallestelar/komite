from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.core.settings import settings


@dataclass
class StoredSignature:
    key: str
    content_type: str
    size_bytes: int
    updated_at: str


class PrivateSignatureStorageService:
    allowed_types = {"image/png", "image/jpeg", "image/webp"}
    max_upload_bytes = 1024 * 1024
    max_width = 900
    max_height = 320

    def base_dir(self) -> Path:
        configured = Path(settings.private_upload_dir)
        if configured.is_absolute():
            return configured
        return Path(__file__).resolve().parents[3] / configured

    def save_signature_asset(self, *, signature_id: str, content: bytes, content_type: str | None) -> StoredSignature:
        return self._save_signature(prefix=f"signatures/assets/{signature_id}", content=content, content_type=content_type)

    def _save_signature(self, *, prefix: str, content: bytes, content_type: str | None) -> StoredSignature:
        if content_type not in self.allowed_types:
            raise ValueError("Formato de firma no permitido. Usa PNG, JPG o WEBP.")
        if len(content) > self.max_upload_bytes:
            raise ValueError("La firma supera el limite de 1 MB.")

        try:
            from PIL import Image, ImageOps
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise RuntimeError("Falta Pillow para procesar la firma.") from exc

        try:
            with Image.open(BytesIO(content)) as image:
                image = ImageOps.exif_transpose(image)
                if max(image.size) > max(self.max_width, self.max_height):
                    image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                if image.mode not in {"RGBA", "LA"}:
                    image = image.convert("RGBA")

                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                normalized = output.getvalue()
        except Exception as exc:
            raise ValueError("No se pudo leer la imagen de firma.") from exc

        key = f"{prefix.strip('/')}/{uuid4()}.png"
        target = self.base_dir() / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(normalized)
        return StoredSignature(
            key=key,
            content_type="image/png",
            size_bytes=len(normalized),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def read(self, key: str | None) -> bytes | None:
        if not key:
            return None
        target = (self.base_dir() / key).resolve()
        base = self.base_dir().resolve()
        if base not in target.parents:
            return None
        if not target.exists() or not target.is_file():
            return None
        return target.read_bytes()

    def delete(self, key: str | None) -> None:
        if not key:
            return
        target = (self.base_dir() / key).resolve()
        base = self.base_dir().resolve()
        if base not in target.parents:
            return
        if target.exists() and target.is_file():
            target.unlink()
