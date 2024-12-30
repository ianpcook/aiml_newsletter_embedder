from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    fields: Optional[List[str]] = None

class SearchResponse(BaseModel):
    header: str
    received_date: datetime
    text_content: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime 