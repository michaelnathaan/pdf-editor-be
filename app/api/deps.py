from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.config import settings
from app.models import EditSession


# Dependency for API key authentication (service-to-service)
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key for service-to-service authentication"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


# Dependency for session token authentication (browser/user)
async def verify_session_token(
    session_id: UUID,
    session_token: str,
    db: AsyncSession = Depends(get_db)
) -> EditSession:
    """Verify session token for browser-based editing"""
    result = await db.execute(
        select(EditSession).where(
            EditSession.id == session_id,
            EditSession.session_token == session_token,
            EditSession.status == "active"
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired session"
        )
    
    # Check if session is expired
    from datetime import datetime
    if session.expires_at < datetime.utcnow():
        session.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Session has expired"
        )
    
    return session


# Get current session from header or query param
async def get_current_session(
    session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Optional[EditSession]:
    """Get current session from token (header or query param)"""
    token_value = session_token or token
    
    if not token_value:
        return None
    
    result = await db.execute(
        select(EditSession).where(
            EditSession.session_token == token_value,
            EditSession.status == "active"
        )
    )
    return result.scalar_one_or_none()