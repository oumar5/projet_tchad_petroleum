import pytest


@pytest.mark.parametrize("path", [
    "/v1/auth/openapi.json",
    "/v1/production/openapi.json",
    "/v1/maintenance/openapi.json",
    "/v1/ml/openapi.json",
    "/v1/etl/openapi.json",
    "/v1/notifications/openapi.json",
    "/docs/openapi.json",
])
def test_openapi_specs_exposed(http_client, path):
    r = http_client.get(path)
    assert r.status_code == 200
    body = r.json()
    assert body.get("openapi", "").startswith("3.")
