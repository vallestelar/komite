from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.auth.dependencies import require_access_token, user_is_komite_employee
from app.models.entities import Bank, Condominium
from app.repositories.user_repository import user_has_condominium
from app.services.edifito_neighbors_import_service import EdifitoNeighborsImportService
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


@router.post("/import-neighbors")
async def import_edifito_neighbors(
    request: Request,
    condominium_id: str = Form(...),
    assignments_file: UploadFile = File(...),
) -> dict:
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

    if not (assignments_file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe cargar un archivo XLSX de asignaciones")

    service = EdifitoNeighborsImportService()
    try:
        result = await service.import_assignments(
            company_id=str(condominium.company_id),
            condominium_id=str(condominium.id),
            content=await assignments_file.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result["condominium_id"] = str(condominium.id)
    result["condominium_name"] = condominium.name
    return result
