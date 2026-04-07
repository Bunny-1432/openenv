# Email Triage Environment — Docker Image
# Self-contained build: does NOT depend on any external registry image.
# Compatible with the pre-submission validation script (docker build at root).

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reproducible dependency installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

WORKDIR /app

# Copy project metadata first (layer cache for deps)
COPY pyproject.toml uv.lock ./

# Copy application code
COPY openenv.yaml ./
COPY models.py ./
COPY client.py ./
COPY server/ ./server/

# Create venv and install all dependencies from lock file (reproducible)
RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --python /app/.venv/bin/python || \
    uv pip install --python /app/.venv/bin/python \
        openenv-core \
        fastapi \
        "uvicorn[standard]" \
        pydantic \
        fastmcp \
        httpx \
        openai

# Activate venv and set Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV ENABLE_WEB_INTERFACE=true

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
