import os
import shutil
import aiofiles
from uuid import UUID

from app.config import settings


class StorageService:
    """Service for handling file storage operations"""
    
    @staticmethod
    def get_upload_path(file_id: UUID, filename: str) -> str:
        """Get path for uploaded file"""
        return os.path.join(settings.upload_dir, f"{file_id}_{filename}")
    
    @staticmethod
    def get_edited_path(session_id: UUID, filename: str) -> str:
        """Get path for edited file"""
        return os.path.join(settings.edited_dir, f"{session_id}_{filename}")
    
    @staticmethod
    def get_session_temp_dir(session_id: UUID) -> str:
        """Get temporary directory for session"""
        temp_dir = os.path.join(settings.temp_dir, str(session_id))
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @staticmethod
    def get_session_image_path(session_id: UUID, image_id: UUID, filename: str) -> str:
        """Get path for session image"""
        session_dir = StorageService.get_session_temp_dir(session_id)
        return os.path.join(session_dir, f"{image_id}_{filename}")
    
    @staticmethod
    async def save_upload_file(file_content: bytes, file_path: str) -> int:
        """Save uploaded file asynchronously"""
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        return len(file_content)
    
    @staticmethod
    async def read_file(file_path: str) -> bytes:
        """Read file asynchronously"""
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
        return False
    
    @staticmethod
    def delete_session_temp_dir(session_id: UUID) -> bool:
        """Delete entire session temporary directory"""
        try:
            session_dir = os.path.join(settings.temp_dir, str(session_id))
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                return True
        except Exception as e:
            print(f"Error deleting session directory {session_id}: {e}")
        return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        if StorageService.file_exists(file_path):
            return os.path.getsize(file_path)
        return 0