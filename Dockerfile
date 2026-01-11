# Repo image for ludolog.
FROM python:3.12.7-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip==24.2 setuptools==75.1.0 wheel==0.44.0

COPY . /app

RUN pip install pytest==8.3.3 pytest-cov==5.0.0 openpyxl==3.1.5

RUN pip install /app

CMD ["pytest", "-q", "/app/tests"]
