# ResumeIQ backend — FastAPI on Render
FROM python:3.12-slim

# PyMuPDF needs these for PDF rendering; python-docx is pure-python.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY db/ ./db/

# Render injects $PORT at runtime; default to 8000 for local docker run.
ENV PORT=8000
EXPOSE 8000

# --workers 2 is a reasonable default for Render's free/starter tiers
# (single vCPU). Bump via WEB_CONCURRENCY env var on larger instances.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY:-2}
