import os
import json
import logging
from typing import Set
from .client import get_weaviate_client

logger = logging.getLogger(__name__)

def get_existing_email_ids() -> Set[str]:
    """Get set of email IDs already in Weaviate"""
    client = get_weaviate_client()
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
                    
            logger.info(f"Found {len(existing)} unique identifiers in Weaviate (includes both email_ids and internal Weaviate IDs)")
            
            count_result = client.query.aggregate("Newsletter").with_meta_count().do()
            total_count = count_result['data']['Aggregate']['Newsletter'][0]['meta']['count']
            logger.info(f"Actual number of unique records in Weaviate: {total_count}")
            
        return existing
    except Exception as e:
        logger.warning(f"Error getting existing records: {e}")
    
    return set()

def load_data():
    """Load newsletter data into Weaviate"""
    client = get_weaviate_client()
    
    # Add diagnostic information
    logger.info("Weaviate client information:")
    logger.info(f"Client: {client.__class__.__module__}.{client.__class__.__name__}")
    logger.info(f"Batch: {client.batch.__class__.__module__}.{client.batch.__class__.__name__}")
    
    data_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'newsletter_records.json'))
    error_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'error_records.json'))
    logger.info(f"Loading data from {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Load existing error records if any
    error_records = {}
    if os.path.exists(error_path):
        try:
            with open(error_path, 'r') as f:
                error_records = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load error records: {e}")
    
    logger.info(f"Found {len(data)} newsletter records in the JSON file")
    logger.info(f"Found {len(error_records)} existing error records")
    
    # Get records actually in Weaviate
    existing_ids = get_existing_email_ids()
    logger.info(f"Found {len(existing_ids)} existing identifiers in Weaviate database")
    
    # Include both records not in Weaviate and records that previously errored
    new_records = [d for d in data if d['id'] not in existing_ids or d['id'] in error_records]
    logger.info(f"Will attempt to load {len(new_records)} records (not in Weaviate or previously errored)")

    if not new_records:
        logger.info("No new records to load")
        if error_records:
            # Clear error records since everything is loaded
            with open(error_path, 'w') as f:
                json.dump({}, f)
        return

    successful_imports = 0
    current_errors = {}
    
    try:
        with client.batch(
            batch_size=2,
            dynamic=True,
            num_workers=1,
            num_retries=3
        ) as batch:
            logger.debug("Successfully initialized batch context")
            for d in new_records:
                try:
                    text_content = ""
                    if 'sections' in d and d['sections']:
                        text_content = "\n\n".join(section.strip() for section in d['sections'] if section.strip())
                    elif 'body' in d and d['body']:
                        text_content = d['body']

                    if not text_content.strip():
                        logger.warning(f"Skipping record {d.get('id', 'unknown')} due to empty content")
                        current_errors[d['id']] = "Empty content"
                        continue

                    header = d.get('subject', '')
                    if not header and 'sections' in d and d['sections']:
                        header = d['sections'][0].strip()

                    if not header.strip():
                        logger.warning(f"Skipping record {d.get('id', 'unknown')} due to empty header")
                        current_errors[d['id']] = "Empty header"
                        continue

                    properties = {
                        "newsletter": d.get("from", "Unknown Newsletter").split('<')[0].strip(),
                        "sender": d.get("from", ""),
                        "header": header,
                        "received_date": d.get("date", ""),
                        "links": [],
                        "text_content": text_content,
                        "email_id": d.get("id", "")
                    }
                    
                    if not properties["email_id"]:
                        logger.warning(f"Skipping record due to missing ID")
                        current_errors[d['id']] = "Missing ID"
                        continue
                        
                    batch.add_data_object(
                        data_object=properties,
                        class_name="Newsletter"
                    )
                    successful_imports += 1
                    
                    if successful_imports % 10 == 0:
                        logger.info(f"Progress: {successful_imports}/{len(new_records)} records processed")
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error importing record {d.get('id', 'unknown')}: {error_msg}")
                    current_errors[d['id']] = error_msg

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Batch processing failed: {error_msg}")
        # Add all remaining records to errors
        for d in new_records[successful_imports:]:
            current_errors[d['id']] = f"Batch failure: {error_msg}"
    finally:
        # Update error records file
        if current_errors:
            with open(error_path, 'w') as f:
                json.dump(current_errors, f, indent=2)
        elif os.path.exists(error_path):
            # If no errors and file exists, clear it
            with open(error_path, 'w') as f:
                json.dump({}, f)
                
        logger.info(f"Import summary:")
        logger.info(f"- Successfully embedded: {successful_imports}")
        logger.info(f"- Failed records: {len(current_errors)}")