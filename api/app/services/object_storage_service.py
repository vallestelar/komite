from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from app.core.settings import settings


@dataclass
class StoredObject:
    key: str
    url: str
    content_type: str | None = None
    size_bytes: int | None = None


class ObjectStorageService:
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }

    def _safe_name(self, file_name: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_name).strip("._")
        return clean or "logo"

    def _build_key(self, company_id: str, file_name: str, content_type: str | None) -> str:
        original_name = self._safe_name(file_name)
        original_suffix = Path(original_name).suffix.lower()
        allowed_suffixes = set(self.ALLOWED_IMAGE_TYPES.values())
        suffix = original_suffix if original_suffix in allowed_suffixes else self.ALLOWED_IMAGE_TYPES.get(content_type or "", "")
        return f"companies/{company_id}/logo/{uuid4()}{suffix}"

    def _build_image_key(self, prefix: str, file_name: str, content_type: str | None) -> str:
        clean_prefix = re.sub(r"[^A-Za-z0-9_./-]+", "_", prefix).strip("/._")
        original_name = self._safe_name(file_name)
        original_suffix = Path(original_name).suffix.lower()
        allowed_suffixes = set(self.ALLOWED_IMAGE_TYPES.values())
        suffix = original_suffix if original_suffix in allowed_suffixes else self.ALLOWED_IMAGE_TYPES.get(content_type or "", "")
        return f"{clean_prefix}/{uuid4()}_{original_name if original_suffix in allowed_suffixes else 'image' + suffix}"

    def _validate_image(self, content_type: str | None, size_bytes: int) -> None:
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError("Formato de logo no permitido. Usa PNG, JPG, WEBP o SVG.")
        max_bytes = 5 * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError("El logo supera el limite de 5 MB.")

    def _validate_evidence_image(self, content_type: str | None) -> None:
        if content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValueError("Formato de foto no permitido. Usa JPG, PNG o WEBP.")

    def _optimize_evidence_image(self, *, file_name: str, content_type: str | None, content: bytes) -> tuple[str, str, bytes]:
        self._validate_evidence_image(content_type)
        max_bytes = settings.max_evidence_image_mb * 1024 * 1024
        max_px = settings.max_evidence_image_px
        if len(content) <= max_bytes:
            return file_name, content_type or "image/jpeg", content

        try:
            from PIL import Image, ImageOps
        except ImportError as exc:
            raise RuntimeError("Falta Pillow para comprimir fotos grandes. Ejecuta pip install -r requirements.txt.") from exc

        with Image.open(BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
            if max(image.size) > max_px:
                image.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")

            quality = max(55, min(95, settings.evidence_image_quality))
            output = BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
            optimized = output.getvalue()

            while len(optimized) > max_bytes and quality > 58:
                quality -= 8
                output = BytesIO()
                image.save(output, format="JPEG", quality=quality, optimize=True, progressive=True)
                optimized = output.getvalue()

        original_stem = Path(self._safe_name(file_name)).stem or "evidencia"
        return f"{original_stem}.jpg", "image/jpeg", optimized

    def _public_url(self, key: str) -> str:
        if settings.storage_public_base_url:
            return f"{settings.storage_public_base_url.rstrip('/')}/{key}"
        return f"/static/uploads/{key}"

    def _save_local(self, key: str, content: bytes, content_type: str | None = None) -> StoredObject:
        static_dir = Path(__file__).resolve().parents[1] / "static" / "uploads"
        target = static_dir / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return StoredObject(key=key, url=self._public_url(key), content_type=content_type, size_bytes=len(content))

    def _save_s3(self, key: str, content: bytes, content_type: str) -> StoredObject:
        if not settings.s3_bucket:
            raise RuntimeError("S3 no esta configurado. Define S3_BUCKET.")

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("Falta boto3. Ejecuta pip install -r requirements.txt.") from exc

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )
        put_kwargs = {
            "Bucket": settings.s3_bucket,
            "Key": key,
            "Body": content,
            "ContentType": content_type,
        }
        if settings.s3_acl:
            put_kwargs["ACL"] = settings.s3_acl
        client.put_object(**put_kwargs)
        return StoredObject(key=key, url=self._public_url(key), content_type=content_type, size_bytes=len(content))

    async def save_company_logo(self, *, company_id: str, file_name: str, content_type: str | None, content: bytes) -> StoredObject:
        self._validate_image(content_type, len(content))
        key = self._build_key(company_id, file_name, content_type)
        if settings.storage_provider.strip().lower() == "s3":
            return self._save_s3(key, content, content_type or "application/octet-stream")
        return self._save_local(key, content, content_type)

    async def save_image(self, *, prefix: str, file_name: str, content_type: str | None, content: bytes) -> StoredObject:
        self._validate_image(content_type, len(content))
        key = self._build_image_key(prefix, file_name, content_type)
        if settings.storage_provider.strip().lower() == "s3":
            return self._save_s3(key, content, content_type or "application/octet-stream")
        return self._save_local(key, content, content_type)

    async def save_evidence_image(self, *, prefix: str, file_name: str, content_type: str | None, content: bytes) -> StoredObject:
        optimized_name, optimized_type, optimized_content = self._optimize_evidence_image(
            file_name=file_name,
            content_type=content_type,
            content=content,
        )
        key = self._build_image_key(prefix, optimized_name, optimized_type)
        if settings.storage_provider.strip().lower() == "s3":
            return self._save_s3(key, optimized_content, optimized_type)
        return self._save_local(key, optimized_content, optimized_type)
