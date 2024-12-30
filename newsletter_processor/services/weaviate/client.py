import weaviate
from ...core.config import get_settings

settings = get_settings()

def get_weaviate_client():
    """Get or create a Weaviate client instance"""
    return weaviate.Client(settings.WEAVIATE_URL) 