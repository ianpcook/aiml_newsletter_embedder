from fastapi import APIRouter, HTTPException
import logging

from ...services.email.newsletter_processor import NewsletterProcessor
from ...core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.post("/refresh")
async def refresh_emails():
    """Manually trigger email processing"""
    try:
        processor = NewsletterProcessor(
            settings.EMAIL_ADDRESS,
            settings.OUTPUT_FILE,
            settings.ERROR_FILE,
            settings.EMAIL_CHECK_INTERVAL
        )
        processed = await processor.process_emails()
        return {"status": "success", "processed_count": processed}
    except Exception as e:
        logger.error(f"Email refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Email refresh failed")
