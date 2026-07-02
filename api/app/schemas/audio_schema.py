from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AudioProcessingResponse(BaseModel):
    attachment_id: UUID
    file_name: str
    file_type: str
    mime_type: Optional[str] = None
    size_bytes: int
    transcription_text: Optional[str] = None
    draft_text: Optional[str] = None
    transcription_ai_request_id: Optional[UUID] = None
    draft_ai_request_id: Optional[UUID] = None
    provider: str
    transcription_model: str
    draft_model: Optional[str] = None
    status: str
    error_message: Optional[str] = None

