#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# pulls/parses email
python main.py || { echo "Error in main.py"; exit 1; }

# create weaviate newsletter schema
python newsletter_processor/newsletter_schema.py || { echo "Error in newsletter_schema.py"; exit 1; }

# load data into weaviate
python newsletter_processor/weaviate_load.py || { echo "Error in weaviate_load.py"; exit 1; }
