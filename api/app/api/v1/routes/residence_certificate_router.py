from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from tortoise.expressions import Q

from app.core.auth.dependencies import require_access_token
from app.core.settings import settings
from app.models.entities import Condominium, Report, ReportVersion, SignatureAsset, SignaturePermission, UnitContact
from app.services.private_signature_storage_service import PrivateSignatureStorageService
from app.services.residence_certificate_service import ResidenceCertificateService


router = APIRouter(
    prefix="/api/v1/residence-certificates",
    tags=["Residence certificates"],
)


class ResidenceCertificateRequest(BaseModel):
    contact_id: UUID
    signature_id: UUID | None = None
    format: str = Field(default="pdf", pattern="^(pdf|docx)$")
    purpose: str | None = Field(default=None, max_length=240)
    nationality: str | None = Field(default=None, max_length=80)


@router.get("/available-signatures")
async def available_signatures(
    request: Request,
    _: None = Depends(require_access_token(require_condominium=True)),
) -> dict:
    condominium = await _current_condominium(request)
    current_company_id = str(condominium.company_id)
    permissions = await SignaturePermission.filter(
        user_id=request.state.user_id,
        status="active",
        can_use=True,
    ).filter(
        Q(company_id=current_company_id) | Q(company_id__isnull=True),
        Q(condominium_id=condominium.id) | Q(condominium_id__isnull=True),
    ).select_related("signature").order_by("signature__name")

    items = []
    for permission in permissions:
        signature = permission.signature
        if signature.status != "active" or not signature.storage_key:
            continue
        if signature.company_id and str(signature.company_id) != current_company_id:
            continue
        if signature.condominium_id and str(signature.condominium_id) != str(condominium.id):
            continue
        items.append(
            {
                "id": str(signature.id),
                "name": signature.name,
                "signer_name": signature.signer_name,
                "signer_position": signature.signer_position,
                "signer_document": signature.signer_document,
            }
        )
    return {"items": items}


@router.post("/generate")
async def generate_residence_certificate(
    payload: ResidenceCertificateRequest,
    request: Request,
    _: None = Depends(require_access_token(require_condominium=True)),
) -> dict:
    condominium = await _current_condominium(request)
    contact = await UnitContact.get_or_none(
        id=payload.contact_id,
        company_id=condominium.company_id,
        condominium_id=condominium.id,
        status="active",
    ).select_related("unit", "unit__building", "user")
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Residente no encontrado en el condominio activo")

    signature = await _authorized_signature_or_none(request, payload.signature_id)
    signature_image = PrivateSignatureStorageService().read(signature.storage_key) if signature else None
    signer = request.state.user
    if signature:
        signer = type(
            "CertificateSigner",
            (),
            {
                "full_name": signature.signer_name,
                "document_number": signature.signer_document,
                "organization_position": signature.signer_position or "Administrador",
            },
        )()

    service = ResidenceCertificateService()
    common_payload = {
        "condominium": condominium,
        "unit": contact.unit,
        "contact": contact,
        "signer": signer,
        "purpose": payload.purpose,
        "nationality": payload.nationality,
        "signature_image": signature_image,
        "komite_logo": _komite_logo_bytes(),
        "company_logo": _company_logo_bytes(getattr(condominium, "company", None)),
    }
    if payload.format == "docx":
        content_base64 = service.build_docx_base64(**common_payload)
        extension = "docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        content_base64 = service.build_pdf_base64(**common_payload)
        extension = "pdf"
        content_type = "application/pdf"

    safe_unit = "".join(char for char in contact.unit.identifier if char.isalnum() or char in ("-", "_")) or "unidad"
    filename = f"certificado_residencia_{safe_unit}.{extension}"
    await _record_certificate_report(
        request=request,
        condominium=condominium,
        contact=contact,
        signature=signature,
        filename=filename,
        file_format=payload.format,
        purpose=payload.purpose,
        nationality=payload.nationality,
    )
    return {
        "filename": filename,
        "content_type": content_type,
        "content_base64": content_base64,
        "contact_name": contact.full_name,
        "unit_identifier": contact.unit.identifier,
        "signed_by": getattr(signer, "full_name", "") or "",
        "has_signature_image": bool(signature_image),
    }


async def _authorized_signature_or_none(request: Request, signature_id: UUID | None) -> SignatureAsset | None:
    if not signature_id:
        return None

    condominium = await _current_condominium(request)
    current_company_id = str(condominium.company_id)
    permission = await SignaturePermission.filter(
        signature_id=signature_id,
        user_id=request.state.user_id,
        status="active",
        can_use=True,
    ).filter(Q(company_id=current_company_id) | Q(company_id__isnull=True)).select_related("signature").first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para usar esta firma")
    if permission.condominium_id and str(permission.condominium_id) != str(condominium.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma no permitida para este condominio")

    signature = permission.signature
    if signature.company_id and str(signature.company_id) != current_company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma no permitida para esta empresa")
    if signature.status != "active" or not signature.storage_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La firma seleccionada no esta activa o no tiene imagen cargada")
    if signature.condominium_id and str(signature.condominium_id) != str(condominium.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma no permitida para este condominio")
    return signature


async def _record_certificate_report(
    *,
    request: Request,
    condominium: Condominium,
    contact: UnitContact,
        signature: SignatureAsset | None,
    filename: str,
    file_format: str,
    purpose: str | None,
    nationality: str | None,
) -> None:
    actor = getattr(request.state.user, "email", None) or getattr(request.state.user, "full_name", None) or "portal"
    issued_at = datetime.now(timezone.utc)
    content = {
        "template": "residence_certificate_v1",
        "resident_name": contact.full_name,
        "resident_document": contact.document_number,
        "unit_identifier": contact.unit.identifier if getattr(contact, "unit", None) else None,
        "purpose": purpose,
        "nationality": nationality,
        "signature_id": str(signature.id) if signature else None,
        "signer_name": signature.signer_name if signature else None,
        "format": file_format,
        "filename": filename,
    }
    metadata = {
        "source": "residence_certificate_tool",
        "format": file_format,
        "filename": filename,
        "resident_name": contact.full_name,
        "unit_identifier": contact.unit.identifier if getattr(contact, "unit", None) else None,
        "signature_id": str(signature.id) if signature else None,
        "signature_name": signature.name if signature else None,
    }
    report = await Report.create(
        company_id=condominium.company_id,
        condominium_id=condominium.id,
        created_by_user_id=request.state.user_id,
        approved_by_id=request.state.user_id,
        report_type="residence_certificate",
        title=f"Certificado de residencia - {contact.full_name}",
        status="issued",
        content=content,
        approved_at=issued_at,
        published_at=issued_at,
        metadata=metadata,
        created_by=actor,
        updated_by=actor,
    )
    await ReportVersion.create(
        company_id=condominium.company_id,
        report_id=report.id,
        version_number=1,
        source="system",
        content=content,
        notes=f"Certificado emitido en formato {file_format.upper()}.",
        created_by=actor,
        updated_by=actor,
    )


async def _current_condominium(request: Request) -> Condominium:
    condominium = await Condominium.get_or_none(id=request.state.condominium_id).select_related("company")
    if not condominium:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condominio activo no encontrado")
    return condominium


def _komite_logo_bytes() -> bytes | None:
    logo_path = Path(__file__).resolve().parents[3] / "static" / "img" / "komite-logo-new.png"
    if not logo_path.exists():
        logo_path = Path(__file__).resolve().parents[3] / "static" / "img" / "komite-logo.png"
    return _read_file_bytes(logo_path)


def _company_logo_bytes(company: object | None) -> bytes | None:
    if not company:
        return None

    uploads_dir = Path(__file__).resolve().parents[3] / "static" / "uploads"
    storage_key = getattr(company, "logo_storage_key", None)
    if storage_key:
        logo = _read_file_bytes(uploads_dir / str(storage_key), base_dir=uploads_dir)
        if logo:
            return logo
        logo = _read_s3_bytes(str(storage_key))
        if logo:
            return logo

    logo_url = str(getattr(company, "logo_url", None) or "")
    if logo_url.startswith("/static/uploads/"):
        return _read_file_bytes(Path(__file__).resolve().parents[3] / "static" / logo_url.removeprefix("/static/"), base_dir=uploads_dir)
    if logo_url.startswith(("http://", "https://")):
        return _read_http_image_bytes(logo_url)
    return None


def _read_s3_bytes(storage_key: str) -> bytes | None:
    if settings.storage_provider.strip().lower() != "s3" or not settings.s3_bucket:
        return None
    try:
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )
        response = client.get_object(Bucket=settings.s3_bucket, Key=storage_key)
        body = response["Body"].read()
        return body if body else None
    except Exception:
        return None


def _read_http_image_bytes(url: str) -> bytes | None:
    try:
        import requests

        response = requests.get(url, timeout=8)
        response.raise_for_status()
        if "svg" in response.headers.get("content-type", "").lower():
            return None
        return response.content
    except Exception:
        return None


def _read_file_bytes(path: Path, base_dir: Path | None = None) -> bytes | None:
    try:
        resolved = path.resolve()
        if base_dir:
            base = base_dir.resolve()
            if resolved != base and base not in resolved.parents:
                return None
        if not resolved.exists() or not resolved.is_file():
            return None
        return resolved.read_bytes()
    except OSError:
        return None
