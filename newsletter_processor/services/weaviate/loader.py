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
                    
            logger.info(f"Found {len(existing)} existing records in Weaviate")
            
            count_result = client.query.aggregate("Newsletter").with_meta_count().do()
            total_count = count_result['data']['Aggregate']['Newsletter'][0]['meta']['count']
            logger.info(f"Total records in Weaviate: {total_count}")
            
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
    logger.info(f"Loading data from {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Found {len(data)} total records in file")
    
    existing_ids = get_existing_email_ids()
    logger.info(f"Found {len(existing_ids)} existing IDs in Weaviate")
    
    new_records = [d for d in data if d['id'] not in existing_ids]
    logger.info(f"Loading {len(new_records)} new records out of {len(data)} total records")

    if not new_records:
        logger.info("No new records to load")
        return

    successful_imports = 0
    skipped_records = 0
    batch_errors = []
    
    def batch_callback(results):
        logger.debug(f"Batch callback received: type={type(results)}, value={results}")
        nonlocal batch_errors
        if results and isinstance(results, (list, tuple)):
            errors = [str(err) for err in results if err is not None]
            if errors:
                batch_errors.extend(errors)
                logger.error(f"Batch errors: {errors}")
        logger.info(f"Batch processed: {len(results) if isinstance(results, (list, tuple)) else 0} items")
        if isinstance(results, (list, tuple)):
            logger.debug(f"Batch details: {results}")
        else:
            logger.debug(f"Unexpected results type: {type(results)}, value: {results}")

    try:
        logger.debug("About to initialize batch processing")
        
        with client.batch(
            batch_size=2,
            callback=batch_callback,
            weaviate_error_retries=3,
            connection_error_retries=3
        ) as batch:
            logger.debug("Successfully initialized batch context")
            for d in new_records:
                try:
                    # Process record logic remains the same
                    text_content = ""
                    if 'sections' in d and d['sections']:
                        text_content = "\n\n".join(section.strip() for section in d['sections'] if section.strip())
                    elif 'body' in d and d['body']:
                        text_content = d['body']

                    if not text_content.strip():
                        logger.warning(f"Skipping record {d.get('id', 'unknown')} due to empty content")
                        skipped_records += 1
                        continue

                    header = d.get('subject', '')
                    if not header and 'sections' in d and d['sections']:
                        header = d['sections'][0].strip()

                    if not header.strip():
                        logger.warning(f"Skipping record {d.get('id', 'unknown')} due to empty header")
                        skipped_records += 1
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
                        skipped_records += 1
                        continue
                        
                    batch.add_data_object(properties, "Newsletter")
                    successful_imports += 1
                    
                    if successful_imports % 10 == 0:
                        logger.info(f"Progress: {successful_imports}/{len(new_records)} records processed")
                        
                except Exception as e:
                    logger.error(f"Error importing record {d.get('id', 'unknown')}: {str(e)}")
                    skipped_records += 1

    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise

    finally:
        logger.info(f"Import summary:")
        logger.info(f"- Successfully embedded: {successful_imports}")
        logger.info(f"- Skipped records: {skipped_records}")
        logger.info(f"- Batch errors: {len(batch_errors)}")
        if batch_errors:
            logger.info("Sample of batch errors:")
            for error in batch_errors[:5]:
                logger.info(f"  - {error}")