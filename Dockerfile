# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Playwright system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
        libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
        fonts-liberation libpangocairo-1.0-0 libpango-1.0-0 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/
RUN pip install --upgrade pip && pip install -e . && pip install -e ".[dev]"

COPY app /app/app
COPY docs /app/docs

RUN playwright install --with-deps chromium

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]