#!/bin/bash
set -e

# Wait for Weaviate to be ready
echo "Waiting for Weaviate..."
timeout 300 bash -c 'until curl -s -f "${WEAVIATE_URL}/v1/.well-known/ready" > /dev/null; do sleep 2; done'

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 