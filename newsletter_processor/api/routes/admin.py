from fastapi import APIRouter, HTTPException
import logging
from weaviate import Client

from ...services.email.newsletter_processor import NewsletterProcessor
from ...services.weaviate.query import get_total_count
from ...services.weaviate.loader import load_data
from ...services.weaviate.newsletter_schema import create_schema_if_not_exists
from ...services.weaviate.client import get_weaviate_client, check_weaviate_ready
from ...core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        client = get_weaviate_client()
        if not client.is_ready():
            return {"status": "degraded", "message": "Weaviate not ready"}
        return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}

@router.get("/count")
async def get_newsletter_count():
    """Get total number of newsletters in the database"""
    try:
        client = get_weaviate_client()
        if not client.is_ready():
            raise HTTPException(
                status_code=503,
                detail="Weaviate service is not ready"
            )
            
        count = get_total_count()
        return {"total_count": count}
    except Exception as e:
        logger.error(f"Database count failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get total count from database: {str(e)}"
        )

@router.post("/refresh")
async def refresh_emails():
    """Manually trigger email processing"""
    try:
        client = get_weaviate_client()
        if not client.is_ready():
            raise HTTPException(
                status_code=503,
                detail="Weaviate service is not ready"
            )
            
        processor = NewsletterProcessor(
            settings.EMAIL_ADDRESS,
            settings.OUTPUT_FILE,
            settings.ERROR_FILE,
            settings.EMAIL_CHECK_INTERVAL
        )
        processed = await processor.process_emails()
        
        if processed > 0:
            try:
                load_data()
            except Exception as e:
                logger.error(f"Data loading failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Email processing succeeded but data loading failed: {str(e)}"
                )
            
        return {"status": "success", "processed_count": processed}
    except Exception as e:
        logger.error(f"Email refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email refresh failed: {str(e)}")

@router.post("/init")
@router.get("/init")
async def initialize_schema():
    """Initialize the Weaviate schema"""
    try:
        client = get_weaviate_client()
        if not client.is_ready():
            raise HTTPException(
                status_code=503,
                detail="Weaviate service is not ready"
            )
            
        result = create_schema_if_not_exists()
        return result
    except Exception as e:
        logger.error(f"Schema creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create schema: {str(e)}"
        )
