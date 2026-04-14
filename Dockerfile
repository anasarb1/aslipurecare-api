# ---------------------------------------------------------------------------
# AslipureCare API — Dockerfile
# ---------------------------------------------------------------------------
# Stage: single-stage production image based on the official slim Python image.
# ---------------------------------------------------------------------------

FROM python:3.11-slim

# Keeps Python from buffering stdout/stderr so logs appear immediately.
ENV PYTHONUNBUFFERED=1 \
    # Prevents Python from writing .pyc files to disk.
    PYTHONDONTWRITEBYTECODE=1

# Set working directory for all subsequent instructions.
WORKDIR /app

# ---------------------------------------------------------------------------
# Install dependencies first (cached layer — only re-runs when
# requirements.txt changes, not on every code change).
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Copy application source code.
# ---------------------------------------------------------------------------
COPY app.py .

# ---------------------------------------------------------------------------
# Expose the port gunicorn will listen on.
# ---------------------------------------------------------------------------
EXPOSE 5000

# ---------------------------------------------------------------------------
# Run with gunicorn:
#   -w 4        → 4 worker processes (good default for a small instance)
#   -b 0.0.0.0  → listen on all interfaces
#   --access-logfile - → stream access logs to stdout
# ---------------------------------------------------------------------------
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
