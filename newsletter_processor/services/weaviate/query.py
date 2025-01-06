import json
from datetime import datetime
from .client import get_weaviate_client

# Define all available fields
NEWSLETTER_FIELDS = ["newsletter", "sender", "header", "received_date", "links", "text_content", "email_id"]

def get_total_count():
    """Get the total number of records in the Newsletter class"""
    client = get_weaviate_client()
    result = client.query.aggregate("Newsletter").with_meta_count().do()
    count = result['data']['Aggregate']['Newsletter'][0]['meta']['count']
    return count

def get_recent_records(limit=5):
    """Get the most recent newsletter records"""
    client = get_weaviate_client()
    result = client.query.get(
        "Newsletter", 
        ["newsletter", "header", "received_date", "sender", "text_content"]
    ).with_sort({"path": ["received_date"], "order": "desc"}).with_limit(limit).do()
    
    return [
        {
            "header": item["header"],
            "received_date": item["received_date"],
            "text_content": item.get("text_content", "")[:500]  # First 500 chars
        }
        for item in result['data']['Get']['Newsletter']
    ]

def search_by_text(search_term, fields=None, limit=3):
    """Search newsletters by content"""
    client = get_weaviate_client()
    if fields is None:
        fields = ["header", "text_content", "received_date"]
    
    result = client.query.get(
        "Newsletter", 
        fields
    ).with_near_text({
        "concepts": [search_term]
    }).with_limit(limit).do()
    
    return [
        {
            "header": item["header"],
            "received_date": item["received_date"],
            "text_content": item.get("text_content", "")[:500]  # First 500 chars
        }
        for item in result['data']['Get']['Newsletter']
    ] 