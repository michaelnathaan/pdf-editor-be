from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict


class SessionCreateRequest(BaseModel):
    expires_in_hours: Optional[int] = Field(default=24, ge=1, le=168)  # 1 hour to 7 days
    callback_url: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = {"can_edit": True, "can_download": True}


class SessionCreateResponse(BaseModel):
    session_id: UUID
    file_id: UUID
    session_token: str
    editor_url: str
    expires_at: datetime
    permissions: Dict[str, bool]
    
    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    id: UUID
    file_id: UUID
    session_token: str
    status: str
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    completed_at: Optional[datetime] = None
    edited_file_path: Optional[str] = None
    edited_file_size: Optional[int] = None
    permissions: Dict[str, bool]
    callback_url: Optional[str] = None
    callback_status: Optional[str] = None
    
    class Config:
        from_attributes = True


class SessionCommitResponse(BaseModel):
    session_id: UUID
    file_id: UUID
    status: str
    edited_file_path: str
    edited_file_size: int
    download_url: str
    completed_at: datetime