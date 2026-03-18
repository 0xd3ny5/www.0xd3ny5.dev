# Build
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Runtime
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system app && \
    useradd --system --gid app --create-home app

COPY --from=builder /install /usr/local

COPY alembic.ini gunicorn.conf.py ./
COPY scripts/ scripts/
COPY static/ static/
COPY backend/ backend/
COPY blog_posts/ blog_posts/

RUN sed -i 's/\r$//' scripts/entrypoint.sh && \
    chmod +x scripts/entrypoint.sh && \
    chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./scripts/entrypoint.sh"]
