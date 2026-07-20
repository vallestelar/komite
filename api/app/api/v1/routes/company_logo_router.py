from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.crud_router_factory import serialize_model
from app.core.auth.dependencies import require_komite_employee
from app.models.entities import Company
from app.schemas.entity_schemas import CompanyOut
from app.services.object_storage_service import ObjectStorageService


router = APIRouter(prefix="/api/v1/companies", tags=["Companies"])


@router.post("/{company_id}/logo", response_model=CompanyOut, dependencies=[Depends(require_komite_employee())])
async def upload_company_logo(company_id: UUID, file: UploadFile = File(...)) -> CompanyOut:
    company = await Company.get_or_none(id=company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")

    content = await file.read()
    try:
        stored = await ObjectStorageService().save_company_logo(
            company_id=str(company.id),
            file_name=file.filename or "logo",
            content_type=file.content_type,
            content=content,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    company.logo_url = stored.url
    company.logo_storage_key = stored.key
    await company.save()
    return CompanyOut(**serialize_model(company))
