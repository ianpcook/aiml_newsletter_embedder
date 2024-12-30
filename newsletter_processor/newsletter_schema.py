import weaviate
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = weaviate.Client("http://localhost:8080")

def clear_schema():
    """Delete the Newsletter class if it exists"""
    try:
        if client.schema.exists("Newsletter"):
            client.schema.delete_class("Newsletter")
            logger.info("Deleted existing Newsletter schema")
    except Exception as e:
        logger.error(f"Error clearing schema: {e}")

def create_schema_if_not_exists():
    # Check if schema exists
    try:
        schema = client.schema.get()
        if any(class_obj["class"] == "Newsletter" for class_obj in schema["classes"]):
            logger.info("Newsletter schema already exists")
            return
    except Exception as e:
        logger.warning(f"Error checking schema: {e}")

    # Create schema only if it doesn't exist
    newsletter_class_obj = {
        "class": "Newsletter",
        "description": "Newsletter class",
        "vectorizer": "text2vec-transformers",
        "properties": [
            {
                "name": "newsletter",
                "description": "The title or name of the newsletter.",
                "dataType": ["text"]
            },
            {
                "name": "sender",
                "description": "The email address or name of the sender.",
                "dataType": ["text"], 
                "moduleConfig": {
                    "text2vec-transformers": {
                        "skip": True,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "header",
                "description": "The header of the section of the newsletter.",
                "dataType": ["text"]
            },
            {
                "name": "received_date",
                "description": "The date when the newsletter was received.",
                "dataType": ["date"]
            },
            {
                "name": "links",
                "description": "The links in the newsletter.",
                "dataType": ["string[]"],
                "moduleConfig": {
                    "text2vec-transformers": {
                        "skip": True,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "text_content",
                "description": "The text content from the newsletter.",
                "dataType": ["string"],
                "moduleConfig": {
                    "text2vec-transformers": {
                        "skip": False,
                        "vectorizePropertyName": True
                    }
                }
            },
            {
                "name": "email_id",
                "description": "ID of email.",
                "dataType": ["string"],
                "moduleConfig": {
                    "text2vec-transformers": {
                        "skip": True,
                        "vectorizePropertyName": False
                    }
                }
            }
        ]
    }

    logger.info("Creating Newsletter schema")
    client.schema.create_class(newsletter_class_obj)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', action='store_true', help='Clear existing schema before creating new one')
    args = parser.parse_args()
    
    if args.clear:
        clear_schema()
    create_schema_if_not_exists()
