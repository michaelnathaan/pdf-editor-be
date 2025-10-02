from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class FileUploadResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    page_count: int
    mime_type: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class FileInfo(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    page_count: int
    mime_type: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True