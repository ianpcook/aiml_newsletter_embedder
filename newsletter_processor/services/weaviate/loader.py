import os
import json
import logging
from typing import Set
from .client import get_weaviate_client

logger = logging.getLogger(__name__)

client = get_weaviate_client()

def get_existing_email_ids() -> Set[str]:
    """Get set of email IDs already in Weaviate"""
    try:
        result = client.query.get(
            "Newsletter", 
            ["email_id", "_additional {id}"]
        ).with_limit(10000).do()
        
        existing = set()
        if result and 'data' in result and 'Get' in result['data']:
            for item in result['data']['Get']['Newsletter']:
                if 'email_id' in item and item['email_id']:
                    existing.add(item['email_id'])
                if '_additional' in item and 'id' in item['_additional']:
                    existing.add(item['_additional']['id'])
                    
            logger.info(f"Found {len(existing)} existing records in Weaviate")
            
            count_result = client.query.aggregate("Newsletter").with_meta_count().do()
            total_count = count_result['data']['Aggregate']['Newsletter'][0]['meta']['count']
            logger.info(f"Total records in Weaviate: {total_count}")
            
        return existing
    except Exception as e:
        logger.warning(f"Error getting existing records: {e}")
    
    return set()

def load_data():
    data_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'newsletter_records.json'))
    logger.info(f"Loading data from {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Found {len(data)} total records in file")
    
    existing_ids = get_existing_email_ids()
    new_records = [d for d in data if d['id'] not in existing_ids]
    logger.info(f"Loading {len(new_records)} new records out of {len(data)} total records")

    if not new_records:
        logger.info("No new records to load")
        return

    successful_imports = 0
    
    # Configure batch settings for better performance and reliability
    with client.batch(
        batch_size=20,          # Reduced batch size
        dynamic=True,           # Enable dynamic batching
        num_workers=8,          # Use multiple workers
        callback=lambda results: logger.info(
            f"Batch processed with {len(results)} results"
            + (f", with errors: {[str(err) for err in results if err]}" if any(results) else "")
        )
    ) as batch:
        for d in new_records:
            try:
                # Extract sections if available, otherwise use full body
                text_content = ""
                if 'sections' in d and d['sections']:
                    # Join all sections with newlines, excluding empty ones
                    text_content = "\n\n".join(section.strip() for section in d['sections'] if section.strip())
                elif 'body' in d and d['body']:
                    text_content = d['body']

                # Extract header/title from subject or first section
                header = d.get('subject', '')
                if not header and 'sections' in d and d['sections']:
                    header = d['sections'][0].strip()

                properties = {
                    "newsletter": d.get("from", "Unknown Newsletter").split('<')[0].strip(),  # Get name part of email
                    "sender": d.get("from", ""),
                    "header": header,
                    "received_date": d.get("date", ""),
                    "links": [],  # Links will be extracted in future enhancement
                    "text_content": text_content,
                    "email_id": d.get("id", "")
                }
                
                if not properties["email_id"]:
                    logger.warning(f"Skipping record due to missing ID")
                    continue
                    
                batch.add_data_object(properties, "Newsletter")
                successful_imports += 1
                
                # Log progress every 10 records
                if successful_imports % 10 == 0:
                    logger.info(f"Progress: {successful_imports}/{len(new_records)} records processed")
                    
            except Exception as e:
                logger.error(f"Error importing record {d.get('id', 'unknown')}: {str(e)}")

    logger.info(f"Successfully embedded {successful_imports} out of {len(new_records)} new records into Weaviate")