# KNG6 — strategy-1 streak12_cheap19 (default 15m BTC up/down; $1 FAK on signal)
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kng6/ ./kng6/

RUN mkdir -p /app/logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENV POLY_DRY_RUN=true

CMD ["python", "-m", "kng6"]
