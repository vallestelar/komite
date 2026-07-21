from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.crud_router_factory import serialize_model
from app.core.auth.dependencies import require_komite_employee
from app.models.entities import SignatureAsset
from app.schemas.entity_schemas import SignatureAssetOut
from app.services.private_signature_storage_service import PrivateSignatureStorageService


router = APIRouter(
    prefix="/api/v1/signature-assets",
    tags=["Signature assets"],
    dependencies=[Depends(require_komite_employee())],
)


@router.post("/{signature_id}/image", response_model=SignatureAssetOut)
async def upload_signature_image(signature_id: UUID, file: UploadFile = File(...)) -> SignatureAssetOut:
    signature = await SignatureAsset.get_or_none(id=signature_id)
    if not signature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firma no encontrada")

    storage = PrivateSignatureStorageService()
    content = await file.read()
    try:
        stored = storage.save_signature_asset(
            signature_id=str(signature.id),
            content=content,
            content_type=file.content_type,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    previous_key = signature.storage_key
    signature.storage_key = stored.key
    signature.content_type = stored.content_type
    signature.size_bytes = stored.size_bytes
    metadata = dict(signature.metadata or {})
    metadata["signature_updated_at"] = stored.updated_at
    signature.metadata = metadata
    await signature.save()
    storage.delete(previous_key)

    return SignatureAssetOut(**serialize_model(signature))
