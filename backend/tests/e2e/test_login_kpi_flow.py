"""Golden path: login → me → KPI."""


def test_me_returns_user(http_client, auth_headers):
    r = http_client.get("/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    payload = r.json()
    assert payload["email"] == "e2e-admin@smartbarrel.td"
    assert isinstance(payload["roles"], list)
    assert isinstance(payload["permissions"], list)


def test_kpis_endpoint_reachable(http_client, auth_headers):
    """The endpoint must respond — content can be empty if DB is fresh."""
    r = http_client.get("/v1/production/kpis?period=30d", headers=auth_headers)
    # 200 with payload, or 403 if seeded user does not have production:read
    assert r.status_code in (200, 403)
    if r.status_code == 200:
        payload = r.json()
        assert "production_total_bbl" in payload
        assert payload["period"] == "30d"


def test_unauthenticated_blocked(http_client):
    r = http_client.get("/v1/auth/me")
    assert r.status_code == 401
