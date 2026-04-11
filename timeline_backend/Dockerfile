FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files & buffer output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CRITICAL FOR CONFERENCE DEMOS: Pre-download HuggingFace model weights during the build phase.
# Doing this prevents the container from pausing for 3 minutes to download models during a cold boot!
RUN python -c "from transformers import pipeline; pipeline('ner', model='dslim/bert-base-NER', aggregation_strategy='simple')"

COPY app/ ./app/

# Automatically handled by GCP Cloud Run via the $PORT env var, but exposed locally on 8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
