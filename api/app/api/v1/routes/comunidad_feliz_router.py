from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from app.core.auth.dependencies import require_access_token, user_is_komite_employee
from app.models.entities import Bank, Condominium
from app.repositories.user_repository import user_has_condominium
from app.services.comunidad_feliz_neighbors_import_service import ComunidadFelizNeighborsImportService
from app.services.comunidad_feliz_processing_service import ComunidadFelizProcessingService

router = APIRouter(
    prefix="/api/v1/comunidad-feliz",
    tags=["Comunidad Feliz"],
)


class ComunidadFelizExportRequest(BaseModel):
    rows: list[dict[str, Any]]


async def _get_allowed_import_condominium(request: Request, condominium_id: str) -> Condominium:
    condominium = await Condominium.get_or_none(id=condominium_id)
    if not condominium:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunidad no encontrada")

    is_komite = await user_is_komite_employee(request.state.user)
    allowed_condominium_ids = {
        str(item.get("id"))
        for item in getattr(request.state, "condominiums", [])
        if isinstance(item, dict) and item.get("id")
    }
    if not is_komite:
        if str(condominium_id) not in allowed_condominium_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Comunidad no permitida para este usuario")
        if not await user_has_condominium(str(request.state.user_id), str(condominium_id)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario no pertenece a esta comunidad")

    return condominium


def _validate_charges_file(charges_file: UploadFile) -> None:
    if not (charges_file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe cargar un archivo XLSX de Comunidad Feliz")


@router.post("/process")
async def process_comunidad_feliz_files(
    _: None = Depends(require_access_token(require_condominium=True)),
    bank_statement: UploadFile = File(...),
    charges_file: UploadFile = File(...),
    bank_id: str | None = Form(default=None),
    bank_name: str | None = Form(default=None),
) -> dict:
    selected_bank_name = (bank_name or "").strip()
    if bank_id:
        bank = await Bank.get_or_none(id=bank_id)
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banco no encontrado",
            )
        selected_bank_name = bank.name

    if not selected_bank_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar un banco.",
        )

    service = ComunidadFelizProcessingService()
    try:
        return service.process(
            bank_name=selected_bank_name,
            bank_statement=await bank_statement.read(),
            bank_filename=bank_statement.filename or "",
            charges_file=await charges_file.read(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/export-ingresos")
async def export_comunidad_feliz_ingresos(
    payload: ComunidadFelizExportRequest,
    _: None = Depends(require_access_token(require_condominium=True)),
) -> dict:
    service = ComunidadFelizProcessingService()
    return {
        "ingresos_filename": "ingresos_comunidad_feliz.xlsx",
        "ingresos_base64": service.build_ingresos_workbook_base64(payload.rows),
    }


@router.post("/import-neighbors/preview")
async def preview_comunidad_feliz_neighbors_import(
    request: Request,
    _: None = Depends(require_access_token()),
    condominium_id: str = Form(...),
    charges_file: UploadFile = File(...),
) -> dict:
    condominium = await _get_allowed_import_condominium(request, condominium_id)
    _validate_charges_file(charges_file)

    service = ComunidadFelizNeighborsImportService()
    try:
        result = await service.preview_charges(
            company_id=str(condominium.company_id),
            condominium_id=str(condominium.id),
            content=await charges_file.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result["condominium_id"] = str(condominium.id)
    result["condominium_name"] = condominium.name
    return result


@router.post("/import-neighbors")
async def import_comunidad_feliz_neighbors(
    request: Request,
    _: None = Depends(require_access_token()),
    condominium_id: str = Form(...),
    charges_file: UploadFile = File(...),
) -> dict:
    condominium = await _get_allowed_import_condominium(request, condominium_id)
    _validate_charges_file(charges_file)

    service = ComunidadFelizNeighborsImportService()
    try:
        result = await service.import_charges(
            company_id=str(condominium.company_id),
            condominium_id=str(condominium.id),
            content=await charges_file.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result["condominium_id"] = str(condominium.id)
    result["condominium_name"] = condominium.name
    return result
