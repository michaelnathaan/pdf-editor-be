from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import os

from app.database import get_db
from app.models import File as FileModel
from app.schemas.file import FileUploadResponse, FileInfo
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.api.deps import verify_api_key
from app.config import settings

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Upload a PDF file
    
    Requires API key authentication
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are allowed. Got: {file_ext}"
        )

    content = await file.read()
    file_size = len(content)

    if file_size > settings.UPLOAD_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.UPLOAD_MAX_SIZE} bytes"
        )

    db_file = FileModel(
        filename=file.filename,
        original_filename=file.filename,
        file_path="",
        file_size=file_size,
        page_count=0,
        mime_type=file.content_type or "application/pdf"
    )
    db.add(db_file)
    await db.flush() 
    
    file_path = StorageService.get_upload_path(db_file.id, file.filename)
    await StorageService.save_upload_file(content, file_path)

    try:
        if not PDFService.validate_pdf(file_path):
            StorageService.delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )
        
        page_count = PDFService.get_page_count(file_path)
        
    except Exception as e:
        StorageService.delete_file(file_path)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing PDF: {str(e)}"
        )

    db_file.file_path = file_path
    db_file.page_count = page_count
    
    await db.commit()
    await db.refresh(db_file)
    
    return db_file


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Get file information
    
    Requires API key authentication
    """
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return db_file


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Download original PDF file
    
    Requires API key authentication
    """
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not StorageService.file_exists(db_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_filename,
        media_type=db_file.mime_type
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_api_key)
):
    """
    Delete a file and all associated data
    
    Requires API key authentication
    """
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id)
    )
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    StorageService.delete_file(db_file.file_path)

    await db.delete(db_file)
    await db.commit()
    
    return None