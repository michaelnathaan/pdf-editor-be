from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models import File, EditSession, EditOperation
from app.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfo,
    SessionCommitResponse
)
from app.services.session_service import SessionService
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.api.deps import verify_api_key, verify_session_token
from app.config import settings

router = APIRouter(prefix="/files/{file_id}/sessions", tags=["sessions"])
direct_router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    file_id: UUID,
    request_data: SessionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Create an editing session for a file
    
    Requires API key authentication
    """
    result = await db.execute(
        select(File).where(File.id == file_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    session_token = SessionService.generate_session_token()

    expires_at = SessionService.calculate_expiry(request_data.expires_in_hours)

    db_session = EditSession(
        file_id=file_id,
        session_token=session_token,
        expires_at=expires_at,
        permissions=request_data.permissions,
        callback_url=request_data.callback_url
    )
    
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    base_url = settings.BACKEND_URL
    if '/api/v1' in base_url:
        base_url = base_url.split('/api/v1')[0]
    
    editor_url = SessionService.build_editor_url(
        db_session.id,
        session_token,
        base_url
    )
    
    return SessionCreateResponse(
        session_id=db_session.id,
        file_id=file_id,
        session_token=session_token,
        editor_url=editor_url,
        expires_at=expires_at,
        permissions=request_data.permissions
    )


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session_info(
    file_id: UUID,
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session information
    
    Requires session token (no API key needed for browser access)
    """
    db_session = await verify_session_token(session_id, session_token, db)
    
    if db_session.file_id != file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File ID mismatch"
        )
    
    return db_session

@direct_router.get("/{session_id}/info")
async def get_session_info_direct(
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session information directly by session_id
    
    Requires session token
    """
    result = await db.execute(
        select(EditSession).where(
            EditSession.id == session_id,
            EditSession.session_token == session_token
        )
    )
    db_session = result.scalar_one_or_none()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if session is expired
    from datetime import datetime
    if db_session.expires_at < datetime.utcnow():
        db_session.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Session has expired"
        )
    
    # Get file info
    result = await db.execute(
        select(File).where(File.id == db_session.file_id)
    )
    db_file = result.scalar_one_or_none()
    
    return {
        "id": db_session.id,
        "file_id": db_session.file_id,
        "file_name": db_file.original_filename if db_file else "Unknown",
        "page_count": db_file.page_count if db_file else 0,
        "session_token": db_session.session_token,
        "status": db_session.status,
        "created_at": db_session.created_at,
        "expires_at": db_session.expires_at,
        "permissions": db_session.permissions,
    }


@router.post("/{session_id}/commit", response_model=SessionCommitResponse)
async def commit_session(
    file_id: UUID,
    session_id: UUID,
    session_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Commit all edits and generate final PDF
    
    Requires session token
    """
    db_session = await verify_session_token(session_id, session_token, db)

    if db_session.file_id != file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File ID mismatch"
        )

    result = await db.execute(
        select(File).where(File.id == file_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    result = await db.execute(
        select(EditOperation)
        .where(EditOperation.session_id == session_id)
        .order_by(EditOperation.operation_order)
    )
    operations = result.scalars().all()

    ops_data = [
        {
            "operation_type": op.operation_type,
            "operation_data": op.operation_data
        }
        for op in operations
    ]

    edited_filename = f"edited_{db_file.filename}"
    edited_path = StorageService.get_edited_path(session_id, edited_filename)

    try:
        PDFService.apply_operations_to_pdf(
            input_pdf_path=db_file.file_path,
            output_pdf_path=edited_path,
            operations=ops_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating edited PDF: {str(e)}"
        )

    edited_size = StorageService.get_file_size(edited_path)

    from datetime import datetime
    db_session.status = "completed"
    db_session.completed_at = datetime.now()
    db_session.edited_file_path = edited_path
    db_session.edited_file_size = edited_size
    
    await db.commit()  # <-- add this right after updating session fields
    await db.refresh(db_session)

    base_url = settings.BACKEND_URL
    download_url = f"{base_url}/api/v1/sessions/{session_id}/download?session_token={session_token}"

    if db_session.callback_url:
        db_session.callback_status = "pending"
        await db.commit()
        
        success = await SessionService.retry_webhook(
            callback_url=db_session.callback_url,
            session_id=session_id,
            file_id=file_id,
            download_url=download_url
        )
        
        db_session.callback_status = "success" if success else "failed"
        await db.commit()

    if StorageService.file_exists(db_file.file_path):
        StorageService.delete_file(db_file.file_path)

    StorageService.delete_session_temp_dir(session_id)
    
    return SessionCommitResponse(
        session_id=session_id,
        file_id=file_id,
        status="completed",
        edited_file_path=edited_path,
        edited_file_size=edited_size,
        download_url=download_url,
        completed_at=db_session.completed_at
    )


@direct_router.get("/{session_id}/download")
async def download_edited_file(
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download edited PDF file
    
    Requires session token
    """
    result = await db.execute(
        select(EditSession).where(
            EditSession.id == session_id,
            EditSession.session_token == session_token
        )
    )
    db_session = result.scalar_one_or_none()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if db_session.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not completed yet"
        )
    
    if not db_session.edited_file_path or not StorageService.file_exists(db_session.edited_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edited file not found"
        )
    
    # Get original filename
    result = await db.execute(
        select(File).where(File.id == db_session.file_id)
    )
    db_file = result.scalar_one_or_none()
    
    filename = f"edited_{db_file.original_filename}" if db_file else "edited.pdf"
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=db_session.edited_file_path,
        filename=filename,
        media_type="application/pdf"
    )