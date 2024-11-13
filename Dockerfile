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

# Copy only the necessary files
COPY api.py .
COPY src/ src/
COPY config/ config/

# Create necessary directories
RUN mkdir -p database logs

# Run FastAPI only
CMD uvicorn api:app --host 0.0.0.0 --port 8080