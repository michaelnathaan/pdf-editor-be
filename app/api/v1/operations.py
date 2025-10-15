from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import EditOperation, EditSession
from app.schemas.operation import OperationCreate, OperationResponse, OperationListResponse
from app.api.deps import verify_session_token

router = APIRouter(prefix="/sessions/{session_id}/operations", tags=["operations"])


@router.post("", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
async def create_operation(
    session_id: UUID,
    session_token: str,
    operation: OperationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new edit operation (for undo/redo)
    
    Requires session token
    """
    db_session = await verify_session_token(session_id, session_token, db)
    
    if not db_session.permissions.get("can_edit", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit permission for this session"
        )
    
    # Get next operation order
    result = await db.execute(
        select(func.max(EditOperation.operation_order))
        .where(EditOperation.session_id == session_id)
    )
    max_order = result.scalar()
    next_order = (max_order or 0) + 1

    valid_types = ["add_image", "move_image", "resize_image", "delete_image", "rotate_image"]
    if operation.operation_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation type. Must be one of: {', '.join(valid_types)}"
        )
    
    # If it's an add_image operation, verify the image exists and update the path
    operation_data = operation.operation_data.copy()
    if operation.operation_type == "add_image" and "image_id" in operation_data:
        from app.models import SessionImage
        
        image_id = operation_data["image_id"]
        result = await db.execute(
            select(SessionImage).where(
                SessionImage.id == UUID(image_id) if isinstance(image_id, str) else image_id,
                SessionImage.session_id == session_id
            )
        )
        db_image = result.scalar_one_or_none()
        
        if db_image:
            # Use the actual file path from the database
            operation_data["image_path"] = db_image.file_path
            print(f"Updated image_path to: {db_image.file_path}")
        else:
            print(f"Warning: Image {image_id} not found in session {session_id}")
    
    # Create operation
    db_operation = EditOperation(
        session_id=session_id,
        operation_order=next_order,
        operation_type=operation.operation_type,
        operation_data=operation_data
    )
    
    db.add(db_operation)
    await db.commit()
    await db.refresh(db_operation)
    
    return db_operation


@router.get("", response_model=OperationListResponse)
async def list_operations(
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all operations for a session (for undo/redo)
    
    Requires session token
    """
    # Verify session
    await verify_session_token(session_id, session_token, db)
    
    # Get all operations
    result = await db.execute(
        select(EditOperation)
        .where(EditOperation.session_id == session_id)
        .order_by(EditOperation.operation_order)
    )
    operations = result.scalars().all()
    
    return OperationListResponse(
        operations=operations,
        total=len(operations)
    )


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operation(
    session_id: UUID,
    operation_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an operation (for undo)
    
    Requires session token
    """
    # Verify session
    db_session = await verify_session_token(session_id, session_token, db)
    
    # Check permissions
    if not db_session.permissions.get("can_edit", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit permission for this session"
        )
    
    # Get operation
    result = await db.execute(
        select(EditOperation).where(
            EditOperation.id == operation_id,
            EditOperation.session_id == session_id
        )
    )
    db_operation = result.scalar_one_or_none()
    
    if not db_operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found"
        )
    
    # Delete operation
    await db.delete(db_operation)
    await db.commit()
    
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_operations(
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all operations (reset to original)
    
    Requires session token
    """
    # Verify session
    db_session = await verify_session_token(session_id, session_token, db)
    
    # Check permissions
    if not db_session.permissions.get("can_edit", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit permission for this session"
        )
    
    # Delete all operations for this session
    result = await db.execute(
        select(EditOperation).where(EditOperation.session_id == session_id)
    )
    operations = result.scalars().all()
    
    for op in operations:
        await db.delete(op)
    
    await db.commit()
    
    return None