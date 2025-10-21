from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import EditSession, File
from app.services.storage_service import StorageService


async def cleanup_expired_sessions():
    """
    Clean up files from expired sessions
    Run this periodically (e.g., daily via cron)
    """
    async with AsyncSessionLocal() as db:
        # Grace period: keep files for 1 hour after session expires
        grace_period = timedelta(hours=1)
        cutoff_time = datetime.utcnow() - grace_period
        
        # Find expired sessions
        result = await db.execute(
            select(EditSession).where(
                EditSession.status.in_(["expired", "completed"]),
                EditSession.expires_at < cutoff_time
            )
        )
        expired_sessions = result.scalars().all()
        
        deleted_count = 0
        for session in expired_sessions:
            try:
                # Delete edited PDF
                if session.edited_file_path:
                    StorageService.delete_file(session.edited_file_path)
                
                # Delete temp directory (if not already deleted)
                StorageService.delete_session_temp_dir(session.id)
                
                # Delete the database record
                await db.delete(session)
                deleted_count += 1
                
            except Exception as e:
                print(f"Error cleaning up session {session.id}: {e}")
        
        await db.commit()
        print(f"Cleaned up {deleted_count} expired sessions")
        return deleted_count


async def cleanup_orphaned_files():
    """
    Clean up files that have no database record
    This handles cases where database deletion succeeded but file deletion failed
    """
    import os
    from pathlib import Path
    
    async with AsyncSessionLocal() as db:
        # Get all session IDs from database
        result = await db.execute(select(EditSession.id))
        active_session_ids = {str(sid) for sid in result.scalars().all()}
        
        # Check temp directory
        temp_dir = Path("storage/temp")
        if temp_dir.exists():
            for session_dir in temp_dir.iterdir():
                if session_dir.is_dir() and session_dir.name not in active_session_ids:
                    # Orphaned directory
                    StorageService.delete_session_temp_dir(session_dir.name)
                    print(f"Deleted orphaned temp dir: {session_dir.name}")
        
        # Check edited directory (files older than 24 hours with no active session)
        edited_dir = Path("storage/edited")
        if edited_dir.exists():
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for file_path in edited_dir.iterdir():
                if file_path.is_file():
                    # Check file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        # Check if associated with active session
                        session_id = file_path.stem.split('_')[0]  # Extract session_id from filename
                        if session_id not in active_session_ids:
                            os.remove(file_path)
                            print(f"Deleted orphaned file: {file_path}")