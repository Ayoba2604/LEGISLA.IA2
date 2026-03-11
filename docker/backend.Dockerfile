# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG INSTALL_ML_RERANKER=0

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

COPY backend/requirements.runtime.txt /tmp/backend-requirements-runtime.txt
COPY backend/requirements.ml.txt /tmp/backend-requirements-ml.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/backend-requirements-runtime.txt && \
    if [ "$INSTALL_ML_RERANKER" = "1" ]; then pip install -r /tmp/backend-requirements-ml.txt; fi

COPY backend ./backend
COPY IA ./IA
COPY alembic.ini ./alembic.ini

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
