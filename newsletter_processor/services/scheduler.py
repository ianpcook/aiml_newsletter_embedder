import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .email.newsletter_processor import NewsletterProcessor
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

async def scheduled_email_check():
    """Scheduled task to check for and process new emails"""
    try:
        logger.info("Starting scheduled email check")
        processor = NewsletterProcessor(
            settings.EMAIL_ADDRESS,
            settings.OUTPUT_FILE,
            settings.ERROR_FILE,
            settings.EMAIL_CHECK_INTERVAL
        )
        await processor.process_emails()
    except ConnectionError as e:
        logger.error(f"Email connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in scheduled email check: {str(e)}")

def start_scheduler():
    """Initialize and start the scheduler"""
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        scheduled_email_check,
        CronTrigger(hour=f"*/{settings.EMAIL_CHECK_INTERVAL}"),
        id="email_check",
        name="Check for new newsletter emails"
    )
    
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler 