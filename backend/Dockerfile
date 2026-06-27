# Çok aşamalı imaj: ortak 'base', geliştirme için 'dev' (test araçları + reload),
# üretim için yalın 'prod'. docker-compose 'dev' hedefini build eder.

# ---- Ortak temel ----
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --upgrade pip

# Kaynak + bağımlılık tanımı (editable kurulumun 'app' paketini görmesi için
# kaynak, kurulumdan ÖNCE kopyalanmalı).
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

# ---- Geliştirme: dev bağımlılıkları (pytest, ruff...) + canlı reload ----
FROM base AS dev
RUN pip install -e ".[dev]"
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

# ---- Üretim: yalın kurulum, reload yok ----
FROM base AS prod
RUN pip install .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
