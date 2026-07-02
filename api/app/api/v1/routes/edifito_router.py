from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.auth.dependencies import require_access_token
from app.models.entities import Bank
from app.services.edifito_processing_service import EdifitoProcessingService

router = APIRouter(
    prefix="/api/v1/edifito",
    tags=["Edifito"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


@router.post("/process")
async def process_edifito_files(
    request: Request,
    bank_statement: UploadFile = File(...),
    assignments_file: UploadFile = File(...),
    charge_detail_file: UploadFile = File(...),
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

    service = EdifitoProcessingService()
    try:
        result = service.process(
            bank_name=selected_bank_name,
            bank_statement=await bank_statement.read(),
            assignments_file=await assignments_file.read(),
            charge_detail_file=await charge_detail_file.read(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    result["condominium_id"] = request.state.condominium_id
    result["bank_name"] = selected_bank_name
    return result
