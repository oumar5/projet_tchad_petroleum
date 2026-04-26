import os

import httpx
import pytest


BASE_URL = os.getenv("E2E_BASE_URL", "http://api.localhost")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def http_client(base_url):
    with httpx.Client(base_url=base_url, timeout=10.0) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(http_client):
    """Bootstrap an admin user and login. The first registered user gets viewer
    by default; for full e2e the admin role must be granted via Alembic seed +
    one extra POST /v1/auth/users/{id}/roles using a service token. Here we
    register a fresh user and assume `*` permissions are granted by ops."""
    creds = {
        "email": "e2e-admin@smartbarrel.td",
        "password": "E2E-Test-Pa$$word-12345",
        "full_name": "E2E Admin",
    }
    http_client.post("/v1/auth/register", json=creds)
    r = http_client.post("/v1/auth/login", json={
        "email": creds["email"], "password": creds["password"],
    })
    r.raise_for_status()
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
