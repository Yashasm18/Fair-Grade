# Use official Python lightweight image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by PyMuPDF and standard build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY agents/ agents/
COPY app.py .

# Expose port (Cloud Run/Render uses 8080 or PORT env var)
EXPOSE 8080

# Memory optimizations for Python:
# 1. Limit MALLOC_ARENA_MAX to reduce memory fragmentation
# 2. Use gunicorn with uvicorn workers for better process management
# 3. Use max-requests to recycle workers and clear potential leaks
ENV MALLOC_ARENA_MAX=2
ENV PYTHONUNBUFFERED=1

# Run with Gunicorn
CMD ["gunicorn", "app:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--max-requests", "20", "--max-requests-jitter", "5", "--timeout", "120"]
