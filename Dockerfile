FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p database config logs

# Make sure the application user has write permissions
RUN chmod -R 777 database logs config

# Run the FastAPI application
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}