import weaviate
import logging
from typing import Optional
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class WeaviateClientManager:
    _instance: Optional[weaviate.Client] = None
    
    @classmethod
    def get_client(cls) -> weaviate.Client:
        """Get or create Weaviate client instance"""
        if cls._instance is None:
            cls._instance = weaviate.Client(
                url=settings.WEAVIATE_URL,
                startup_period=30,
                additional_headers={
                    "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
                }
            )
        return cls._instance
    
    @classmethod
    def check_ready(cls) -> bool:
        """Check if Weaviate is ready to accept connections"""
        try:
            client = cls.get_client()
            return bool(client.is_ready)
        except Exception as e:
            logger.error(f"Error checking Weaviate readiness: {str(e)}")
            return False

# Convenience functions
def get_weaviate_client() -> weaviate.Client:
    return WeaviateClientManager.get_client()

def check_weaviate_ready() -> bool:
    return WeaviateClientManager.check_ready() 