FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api ./api
COPY producer ./producer
COPY processor ./processor
COPY cloud_log_pipeline ./cloud_log_pipeline
COPY infra ./infra

RUN pip install --no-cache-dir .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
