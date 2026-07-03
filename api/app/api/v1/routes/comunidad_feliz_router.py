from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.auth.dependencies import require_access_token
from app.models.entities import Bank
from app.services.comunidad_feliz_processing_service import ComunidadFelizProcessingService

router = APIRouter(
    prefix="/api/v1/comunidad-feliz",
    tags=["Comunidad Feliz"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class ComunidadFelizExportRequest(BaseModel):
    rows: list[dict[str, Any]]


@router.post("/process")
async def process_comunidad_feliz_files(
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
async def export_comunidad_feliz_ingresos(payload: ComunidadFelizExportRequest) -> dict:
    service = ComunidadFelizProcessingService()
    return {
        "ingresos_filename": "ingresos_comunidad_feliz.xlsx",
        "ingresos_base64": service.build_ingresos_workbook_base64(payload.rows),
    }
