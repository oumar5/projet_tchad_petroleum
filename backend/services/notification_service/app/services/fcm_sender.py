"""Firebase Cloud Messaging sender (stub for v3 — branchera firebase-admin
quand les credentials seront configurés)."""
import json
import logging
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project}/messages:send"


class FcmSender:
    def __init__(self, credentials_path: str | None):
        self.credentials_path = credentials_path
        self._project_id: str | None = None
        if credentials_path and Path(credentials_path).exists():
            data = json.loads(Path(credentials_path).read_text())
            self._project_id = data.get("project_id")

    @property
    def enabled(self) -> bool:
        return self._project_id is not None

    async def send(self, *, fcm_token: str, title: str, body: str,
                   data: dict | None = None) -> bool:
        if not self.enabled:
            log.info("fcm.disabled (no credentials) — skipping send to %s", fcm_token[:6])
            return False
        # Real implementation would mint an OAuth token from the service account
        # and POST to FCM_ENDPOINT. Left as a stub to avoid hardcoding secrets.
        log.info("fcm.send", extra={"to": fcm_token[:6], "title": title})
        async with httpx.AsyncClient() as _client:
            # placeholder — actual call requires google-auth + token exchange
            return True
