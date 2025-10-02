from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class ImageUploadResponse(BaseModel):
    id: UUID
    session_id: UUID
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    uploaded_at: datetime
    image_url: str
    
    class Config:
        from_attributes = True