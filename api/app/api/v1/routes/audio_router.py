from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.auth.dependencies import require_komite_employee
from app.schemas.audio_schema import AudioProcessingResponse
from app.services.audio_processing_service import AudioProcessingService

router = APIRouter(
    prefix="/api/v1/audio",
    tags=["Audio"],
    dependencies=[Depends(require_komite_employee())],
)


def _parse_optional_uuid(value: Optional[str], field_name: str) -> Optional[UUID]:
    if value is None:
        return None

    clean = value.strip()
    if not clean:
        return None

    try:
        return UUID(clean)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe ser un UUID valido",
        )


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    clean = value.strip()
    if not clean or clean.lower() == "string":
        return None

    return clean


@router.post("/transcriptions", response_model=AudioProcessingResponse)
async def upload_audio_for_transcription(
    request: Request,
    file: UploadFile = File(...),
    condominium_id: Optional[str] = Form(default=None),
    incident_id: Optional[str] = Form(default=None),
    task_id: Optional[str] = Form(default=None),
    inspection_id: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
    transcription_prompt: Optional[str] = Form(default=None),
    draft_prompt: Optional[str] = Form(default=None),
    generate_draft: bool = Form(default=True),
) -> AudioProcessingResponse:
    service = AudioProcessingService()

    try:
        return await service.process_audio(
            upload=file,
            user_id=request.state.user_id,
            condominium_id=_parse_optional_uuid(condominium_id, "condominium_id"),
            incident_id=_parse_optional_uuid(incident_id, "incident_id"),
            task_id=_parse_optional_uuid(task_id, "task_id"),
            inspection_id=_parse_optional_uuid(inspection_id, "inspection_id"),
            language=_clean_optional_text(language),
            transcription_prompt=_clean_optional_text(transcription_prompt),
            draft_prompt=_clean_optional_text(draft_prompt),
            generate_draft=generate_draft,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
