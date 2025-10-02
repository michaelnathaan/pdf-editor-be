from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, List


class OperationCreate(BaseModel):
    operation_type: str = Field(..., description="Type of operation: add_image, move_image, resize_image, delete_image, rotate_image")
    operation_data: Dict[str, Any] = Field(..., description="Operation-specific data")


class OperationResponse(BaseModel):
    id: UUID
    session_id: UUID
    operation_order: int
    operation_type: str
    operation_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OperationListResponse(BaseModel):
    operations: List[OperationResponse]
    total: int