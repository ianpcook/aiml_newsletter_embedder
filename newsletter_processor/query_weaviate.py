import weaviate
import json
from datetime import datetime

def print_separator():
    print("\n" + "="*50 + "\n")

# Initialize the client
client = weaviate.Client("http://localhost:8080")

# Define all available fields
NEWSLETTER_FIELDS = ["newsletter", "sender", "header", "received_date", "links", "text_content", "email_id"]

def get_total_count():
    """Get the total number of records in the Newsletter class"""
    result = client.query.aggregate("Newsletter").with_meta_count().do()
    count = result['data']['Aggregate']['Newsletter'][0]['meta']['count']
    print(f"Total number of records in Newsletter class: {count}")

def get_recent_records(limit=5):
    """Get the most recent newsletter records"""
    result = client.query.get(
        "Newsletter", 
        ["newsletter", "header", "received_date", "sender"]
    ).with_sort({"path": ["received_date"], "order": "desc"}).with_limit(limit).do()
    
    print(f"\nMost recent {limit} records:")
    for item in result['data']['Get']['Newsletter']:
        print(f"\nHeader: {item['header']}")
        print(f"Date: {item['received_date']}")
        print(f"From: {item['sender']}")

def search_by_text(search_term, fields=None, limit=3):
    """Search newsletters by content
    
    Args:
        search_term (str): The text to search for
        fields (list[str], optional): Fields to retrieve. Defaults to ["header", "text_content", "received_date"]
        limit (int, optional): Maximum number of results. Defaults to 3
    """
    if fields is None:
        fields = ["header", "text_content", "received_date"]
    
    result = client.query.get(
        "Newsletter", 
        fields
    ).with_near_text({
        "concepts": [search_term]
    }).with_limit(limit).do()
    
    print(f"\nSearch results for '{search_term}':")
    for item in result['data']['Get']['Newsletter']:
        print(f"\nHeader: {item['header']}")
        print(f"Date: {item['received_date']}")
        if 'text_content' in item:
            print(f"Content snippet: {item['text_content'][:200]}...")

if __name__ == "__main__":
    print("Weaviate Database Query Tool")
    print_separator()
    
    # Get total count
    get_total_count()
    print_separator()
    
    # Get recent records
    get_recent_records(5)
    print_separator()
    
    # Example semantic search
    search_term = "emotions"
    search_by_text(search_term)
