from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...core.config import get_settings
from ...services.weaviate.query import search_by_text, get_recent_records
from ..models import SearchRequest, SearchResponse

router = APIRouter()
settings = get_settings()

@router.post("/search", response_model=List[SearchResponse])
async def search_newsletters(request: SearchRequest):
    try:
        results = search_by_text(
            request.query,
            fields=request.fields or ["header", "text_content", "received_date"],
            limit=request.limit
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )

@router.get("/recent", response_model=List[SearchResponse])
async def get_recent(limit: int = 5):
    try:
        return get_recent_records(limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch recent records"
        ) 