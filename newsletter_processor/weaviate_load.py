import weaviate
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

client = weaviate.Client("http://localhost:8080")

def get_existing_email_ids():
    """Get all existing email IDs from Weaviate"""
    query = """
    {
        Get {
            Newsletter {
                email_id
            }
        }
    }
    """
    result = client.query.raw(query)
    if result and 'data' in result and 'Get' in result['data'] and 'Newsletter' in result['data']['Get']:
        return {item['email_id'] for item in result['data']['Get']['Newsletter']}
    return set()

data_path = os.path.abspath(os.path.join(os.getcwd(), 'data', 'newsletter_records.json'))
with open(data_path, 'r') as f:
    data = json.load(f)

# Get existing email IDs
existing_ids = get_existing_email_ids()
logging.info(f"Found {len(existing_ids)} existing records in Weaviate")

new_records = 0
with client.batch as batch:
    batch.batch_size=100
    # Batch import all Records
    print("loading records")
    for i, d in enumerate(data):
        if d['id'] not in existing_ids:
            properties = {
                "newsletter": "TLDR Newsletter",
                "sender": d["from"],
                "header": d["title"],
                "received_date": d["date"],
                "links": d.get("links", []),
                "text_content": d["description"],
                "email_id": d["id"]
            }
            # this next thing produces logs
            client.batch.add_data_object(properties, "Newsletter")
            new_records += 1

logging.info(f"Added {new_records} new records to Weaviate")
