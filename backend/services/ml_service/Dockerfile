FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY shared/requirements.txt /app/shared/requirements.txt
COPY services/ml_service/requirements.txt /app/services/ml_service/requirements.txt
RUN pip install -r /app/shared/requirements.txt -r /app/services/ml_service/requirements.txt
COPY shared /app/shared
COPY services/ml_service /app/services/ml_service
RUN mkdir -p /app/models && useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "services.ml_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
