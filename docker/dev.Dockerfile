FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    pip install --no-cache-dir "uv>=0.1.13" && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /workspace/

RUN uv pip install --system -e . && \
    uv pip install --system -e .[dev]

COPY app /workspace/app
COPY docs /workspace/docs
COPY tests /workspace/tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

