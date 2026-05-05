"""Shared CORS attachment for SmartBarrel services."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DEV_ORIGIN_REGEX = (
    r"^https?://"
    r"(localhost(:\d+)?"             # localhost any port
    r"|127\.0\.0\.1(:\d+)?"          # 127.0.0.1 any port
    r"|api\.localhost"               # Traefik dev host
    r"|.*\.smartbarrel\.td"          # prod (legacy domain)
    r"|smart-barrel\.web\.app"       # Firebase Hosting (prod)
    r"|smart-barrel\.firebaseapp\.com"
    r"|.*\.oumarbenlol\.com)"        # unified-stack subdomains
    r"$"
)


def attach_cors(app: FastAPI, *, origins: list[str] | None = None) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or [],
        allow_origin_regex=DEV_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
