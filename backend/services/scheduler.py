"""Background task scheduler for automated email digest sending"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler

async def scheduled_digest_job(db):
    """Job that runs on schedule to send weekly digests"""
    from services.email_digest import process_weekly_digests
    
    logger.info("Starting scheduled weekly digest job...")
    
    try:
        # Check if digest is enabled
        config = await db.admin_settings.find_one({"type": "email_digest_config"})
        if not config or not config.get("enabled", False):
            logger.info("Email digest is disabled - skipping")
            return
        
        # Process and send digests
        result = await process_weekly_digests(db)
        
        # Update last sent time
        await db.admin_settings.update_one(
            {"type": "email_digest_config"},
            {
                "$set": {"last_sent": datetime.now(timezone.utc).isoformat()},
                "$inc": {"total_sent": result["sent"]}
            }
        )
        
        logger.info(f"Weekly digest job completed: {result}")
        
    except Exception as e:
        logger.error(f"Error in scheduled digest job: {str(e)}")

def setup_digest_scheduler(db, day_of_week: str = "monday", hour: int = 9):
    """Setup the scheduler with the configured schedule"""
    global scheduler
    
    # Map day names to cron day numbers
    day_map = {
        "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun"
    }
    
    cron_day = day_map.get(day_of_week.lower(), "mon")
    
    sched = get_scheduler()
    
    # Remove existing job if any
    try:
        sched.remove_job("weekly_digest")
    except:
        pass
    
    # Add new job with updated schedule
    sched.add_job(
        lambda: asyncio.create_task(scheduled_digest_job(db)),
        CronTrigger(day_of_week=cron_day, hour=hour, minute=0),
        id="weekly_digest",
        name="Weekly Email Digest",
        replace_existing=True
    )
    
    logger.info(f"Scheduled weekly digest for {day_of_week} at {hour}:00 UTC")

def start_scheduler():
    """Start the scheduler if not already running"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Background scheduler started")

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
