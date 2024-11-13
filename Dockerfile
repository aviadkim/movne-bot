FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p database config logs

# Set environment variables
ENV PORT=8080

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]