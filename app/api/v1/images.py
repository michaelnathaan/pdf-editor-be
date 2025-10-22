from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os

from app.database import get_db
from app.models import SessionImage
from app.schemas.image import ImageUploadResponse
from app.services.storage_service import StorageService
from app.services.image_service import ImageService
from app.api.deps import verify_session_token
from app.config import settings

router = APIRouter(prefix="/sessions/{session_id}/images", tags=["images"])


@router.post("", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    session_id: UUID,
    session_token: str,
    image: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an image to add to the PDF
    
    Requires session token
    """
    db_session = await verify_session_token(session_id, session_token, db)

    if not db_session.permissions.get("can_edit", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit permission for this session"
        )

    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )

    content = await image.read()
    file_size = len(content)
    
    max_image_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Max size: {max_image_size} bytes"
        )
    
    db_image = SessionImage(
        session_id=session_id,
        original_filename=image.filename,
        stored_filename="",
        file_path="",
        file_size=file_size,
        mime_type=image.content_type or "image/jpeg"
    )
    db.add(db_image)
    await db.flush()

    stored_filename = f"{db_image.id}_{image.filename}"
    image_path = StorageService.get_session_image_path(
        session_id,
        db_image.id,
        image.filename
    )
    
    await StorageService.save_upload_file(content, image_path)

    try:
        if not ImageService.validate_image(image_path):
            StorageService.delete_file(image_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        width, height = ImageService.get_image_dimensions(image_path)
        mime_type = ImageService.get_mime_type(image_path)
        
    except Exception as e:
        StorageService.delete_file(image_path)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )

    db_image.stored_filename = stored_filename
    db_image.file_path = image_path
    db_image.width = width
    db_image.height = height
    db_image.mime_type = mime_type
    
    await db.commit()
    await db.refresh(db_image)

    base_url = settings.BACKEND_URL
    image_url = f"{base_url}/api/v1/sessions/{session_id}/images/{db_image.id}?session_token={session_token}"
    
    return ImageUploadResponse(
        id=db_image.id,
        session_id=db_image.session_id,
        original_filename=db_image.original_filename,
        stored_filename=db_image.stored_filename,
        file_size=db_image.file_size,
        mime_type=db_image.mime_type,
        width=db_image.width,
        height=db_image.height,
        uploaded_at=db_image.uploaded_at,
        image_url=image_url
    )


@router.get("/{image_id}")
async def get_image(
    session_id: UUID,
    image_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get an uploaded image
    
    Requires session token
    """
    from sqlalchemy import select
    from fastapi.responses import FileResponse
    
    await verify_session_token(session_id, session_token, db)

    result = await db.execute(
        select(SessionImage).where(
            SessionImage.id == image_id,
            SessionImage.session_id == session_id
        )
    )
    db_image = result.scalar_one_or_none()
    
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if not StorageService.file_exists(db_image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found in storage"
        )
    
    return FileResponse(
        path=db_image.file_path,
        media_type=db_image.mime_type,
        filename=db_image.original_filename
    )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    session_id: UUID,
    image_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an uploaded image
    
    Requires session token
    """
    from sqlalchemy import select

    db_session = await verify_session_token(session_id, session_token, db)

    if not db_session.permissions.get("can_edit", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit permission for this session"
        )

    result = await db.execute(
        select(SessionImage).where(
            SessionImage.id == image_id,
            SessionImage.session_id == session_id
        )
    )
    db_image = result.scalar_one_or_none()
    
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    StorageService.delete_file(db_image.file_path)

    await db.delete(db_image)
    await db.commit()
    
    return None