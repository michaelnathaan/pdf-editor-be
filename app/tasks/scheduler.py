import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.tasks.cleanup import cleanup_expired_sessions, cleanup_orphaned_files


scheduler = AsyncIOScheduler()

# Run cleanup every hour
scheduler.add_job(
    cleanup_expired_sessions,
    'interval',
    hours=1,
    id='cleanup_expired_sessions'
)

# Run orphaned file cleanup daily at 3 AM
scheduler.add_job(
    cleanup_orphaned_files,
    'cron',
    hour=3,
    minute=0,
    id='cleanup_orphaned_files'
)


def start_scheduler():
    """Start the background scheduler"""
    scheduler.start()
    print("📅 Cleanup scheduler started")


def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    print("📅 Cleanup scheduler stopped")