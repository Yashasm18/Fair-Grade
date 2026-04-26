# ─── Build Stage ────────────────────────────────────────────────────────────
# Use a full image to compile native deps (PyMuPDF, etc.)
FROM python:3.10-slim AS builder

WORKDIR /build

# Install system build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into a dedicated prefix so we can copy just them
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime Stage ───────────────────────────────────────────────────────────
# Slim final image — no build tools, smaller attack surface, smaller size
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy compiled packages from builder
COPY --from=builder /install /usr/local

# Runtime system libs still needed by PyMuPDF (libmupdf shared libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY agents/ agents/
COPY app.py .

# ─── Python runtime optimizations ───────────────────────────────────────────
# Prevent .pyc file generation (saves disk I/O on read-only containers)
ENV PYTHONDONTWRITEBYTECODE=1
# Force stdout/stderr to be unbuffered (essential for log streaming)
ENV PYTHONUNBUFFERED=1
# Reduce glibc memory fragmentation (important on memory-constrained hosts)
ENV MALLOC_ARENA_MAX=2

# Expose the port Cloud Run / Render expects
EXPOSE 8080

# ─── Process Manager ─────────────────────────────────────────────────────────
# Gunicorn with uvicorn workers:
#   --workers 2     — two processes handle concurrent requests without GIL
#                     contention; avoids blocking event loop on sync Gemini calls
#                     (safe on Render's 512 MB free tier)
#   --worker-class  — uvicorn.workers.UvicornWorker for ASGI/FastAPI support
#   --timeout 120   — generous timeout for Gemini OCR on large images
#   --max-requests  — recycle workers periodically to clear any memory drift
CMD ["gunicorn", "app:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "120", \
     "--max-requests", "50", \
     "--max-requests-jitter", "10"]
