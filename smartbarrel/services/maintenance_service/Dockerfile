FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY shared/requirements.txt /app/shared/requirements.txt
COPY services/maintenance_service/requirements.txt /app/services/maintenance_service/requirements.txt
RUN pip install -r /app/shared/requirements.txt -r /app/services/maintenance_service/requirements.txt
COPY shared /app/shared
COPY services/maintenance_service /app/services/maintenance_service
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "services.maintenance_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
