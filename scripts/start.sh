#!/bin/bash
set -e

# Wait for Weaviate to be ready with increased timeout and better feedback
echo "Waiting for Weaviate..."
max_retries=30
retry_count=0

while ! curl -s -f "${WEAVIATE_URL}/v1/.well-known/ready" > /dev/null; do
    if [ $retry_count -eq $max_retries ]; then
        echo "Weaviate failed to become ready in time"
        exit 1
    fi
    echo "Waiting for Weaviate... (attempt $((retry_count+1))/$max_retries)"
    sleep 2
    retry_count=$((retry_count+1))
done

echo "Weaviate is ready!"

# Start the FastAPI application with debug logging
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level debug 