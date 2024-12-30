FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY newsletter_processor/ ./newsletter_processor/
COPY scripts/ ./scripts/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Make scripts executable
RUN chmod +x ./scripts/start.sh ./scripts/healthcheck.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ./scripts/healthcheck.sh

# Start the service
CMD ["./scripts/start.sh"] 