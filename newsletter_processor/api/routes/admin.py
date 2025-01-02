from fastapi import APIRouter, HTTPException
import logging

from ...services.email.newsletter_processor import NewsletterProcessor
from ...services.weaviate.query import get_total_count
from ...services.weaviate.loader import load_data
from ...core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.get("/count")
async def get_newsletter_count():
    """Get total number of newsletters in the database"""
    try:
        count = get_total_count()
        return {"total_count": count}
    except Exception as e:
        logger.error(f"Database count failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get total count from database"
        )

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
        
        # Load the processed emails into Weaviate
        if processed > 0:
            load_data()
            
        return {"status": "success", "processed_count": processed}
    except Exception as e:
        logger.error(f"Email refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Email refresh failed")
