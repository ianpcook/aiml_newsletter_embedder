from pydantic import BaseSettings, Field
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "newsletter-processor"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Weaviate Configuration
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    WEAVIATE_API_KEY: Optional[str] = Field(None, env="WEAVIATE_API_KEY")
    
    # Email Configuration
    EMAIL_CHECK_INTERVAL: int = Field(6, env="EMAIL_CHECK_INTERVAL")  # hours
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 