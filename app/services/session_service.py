import secrets
import httpx
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

from app.config import settings


class SessionService:
    """Service for session management operations"""
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def calculate_expiry(hours: int = None) -> datetime:
        """Calculate session expiry datetime"""
        hours = hours or settings.SESSION_EXPIRY_HOURS
        return datetime.utcnow() + timedelta(hours=hours)
    
    @staticmethod
    def build_editor_url(session_id: UUID, session_token: str, base_url: str = None) -> str:
        """Build the editor URL for frontend"""
        # In production, this would be your frontend URL
        # For now, using a placeholder
        base = base_url or f"http://localhost:5173"
        return f"{base}/edit/{session_id}?token={session_token}"
    
    @staticmethod
    async def send_webhook(
        callback_url: str,
        session_id: UUID,
        file_id: UUID,
        download_url: str,
        status: str = "completed"
    ) -> bool:
        """
        Send webhook notification to callback URL (e.g., Teedy)
        
        Payload:
        {
            "session_id": "uuid",
            "file_id": "uuid",
            "status": "completed",
            "download_url": "https://...",
            "completed_at": "2025-10-03T10:30:00Z"
        }
        """
        try:
            payload = {
                "session_id": str(session_id),
                "file_id": str(file_id),
                "status": status,
                "download_url": download_url,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                return response.status_code in [200, 201, 202, 204]
                
        except Exception as e:
            print(f"Error sending webhook to {callback_url}: {str(e)}")
            return False
    
    @staticmethod
    async def retry_webhook(
        callback_url: str,
        session_id: UUID,
        file_id: UUID,
        download_url: str,
        max_retries: int = None
    ) -> bool:
        """Retry webhook with exponential backoff"""
        max_retries = max_retries or settings.WEBHOOK_RETRY_ATTEMPTS
        
        for attempt in range(max_retries):
            success = await SessionService.send_webhook(
                callback_url, session_id, file_id, download_url
            )
            
            if success:
                return True
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s, etc.
        
        return False