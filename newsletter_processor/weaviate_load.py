import weaviate
import os
import json
import logging
from typing import Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = weaviate.Client("http://localhost:8080")

def get_existing_email_ids() -> Set[str]:
    """Get set of email IDs already in Weaviate"""
    try:
        # Get both email_id and id fields to catch all records
        result = client.query.get(
            "Newsletter", 
            ["email_id", "_additional {id}"]
        ).with_limit(10000).do()
        
        existing = set()
        if result and 'data' in result and 'Get' in result['data']:
            for item in result['data']['Get']['Newsletter']:
                if 'email_id' in item and item['email_id']:
                    existing.add(item['email_id'])
                # Also store Weaviate's internal ID
                if '_additional' in item and 'id' in item['_additional']:
                    existing.add(item['_additional']['id'])
                    
            logger.info(f"Found {len(existing)} existing records in Weaviate")
            
            # Log total count for comparison
            count_result = client.query.aggregate("Newsletter").with_meta_count().do()
            total_count = count_result['data']['Aggregate']['Newsletter'][0]['meta']['count']
            logger.info(f"Total records in Weaviate (including those without email_id): {total_count}")
            
        return existing
    except Exception as e:
        logger.warning(f"Error getting existing records: {e}")
    
    return set()

def load_data():
    data_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'newsletter_records.json'))
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Get existing records
    existing_ids = get_existing_email_ids()
    
    # Filter to new records only
    new_records = [d for d in data if d['id'] not in existing_ids]
    logger.info(f"Loading {len(new_records)} new records out of {len(data)} total records")

    if not new_records:
        logger.info("No new records to load")
        return

    with client.batch as batch:
        batch.batch_size=100
        for d in new_records:
            properties = {
                "newsletter": "TLDR Newsletter",
                "sender": d.get("from", ""),
                "header": d.get("title", ""),
                "received_date": d.get("date", ""),
                "links": d.get("links", []),
                "text_content": d.get("description", ""),
                "email_id": d.get("id", "")
            }
            
            # Skip records with missing required fields
            if not properties["header"] or not properties["email_id"]:
                logger.warning(f"Skipping record due to missing required fields: {d.get('id', 'unknown id')}")
                continue
                
            client.batch.add_data_object(properties, "Newsletter")

    logger.info(f"Successfully loaded {len(new_records)} new records")

if __name__ == "__main__":
    load_data()
