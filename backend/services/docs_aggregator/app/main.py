"""Aggregates OpenAPI specs from all services and serves a unified Swagger UI."""
import asyncio

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

UPSTREAMS = {
    "auth": "http://auth-service:8000/v1/auth/openapi.json",
    "production": "http://production-service:8000/v1/production/openapi.json",
    "maintenance": "http://maintenance-service:8000/v1/maintenance/openapi.json",
    "ml": "http://ml-service:8000/v1/ml/openapi.json",
    "etl": "http://etl-service:8000/v1/etl/openapi.json",
    "notifications": "http://notification-service:8000/v1/notifications/openapi.json",
}

app = FastAPI(title="SmartBarrel — Docs Aggregator", version="3.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "docs-aggregator"}


async def _fetch_spec(client: httpx.AsyncClient, url: str) -> dict:
    try:
        r = await client.get(url, timeout=5.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e), "_url": url}


@app.get("/docs/openapi.json")
async def consolidated_openapi() -> JSONResponse:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_fetch_spec(client, u) for u in UPSTREAMS.values()])

    merged = {
        "openapi": "3.0.3",
        "info": {
            "title": "SmartBarrel — Consolidated API",
            "version": "3.0.0",
            "description": "OpenAPI spec consolidé de tous les microservices.",
        },
        "paths": {},
        "components": {"schemas": {}},
        "tags": [],
    }
    for name, spec in zip(UPSTREAMS.keys(), results):
        if "_error" in spec:
            continue
        merged["paths"].update(spec.get("paths", {}))
        merged["components"]["schemas"].update(
            spec.get("components", {}).get("schemas", {})
        )
        merged["tags"].extend(spec.get("tags", []) or [{"name": name}])
    return JSONResponse(merged)


@app.get("/docs", response_class=HTMLResponse)
async def docs_ui() -> HTMLResponse:
    return HTMLResponse("""
<!DOCTYPE html>
<html><head><title>SmartBarrel API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
</head><body>
<div id="swagger"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({ url: "/docs/openapi.json", dom_id: "#swagger" });
</script>
</body></html>
""")
