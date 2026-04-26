"""JWT validation shared by all microservices (RS256, public key)."""
from pathlib import Path
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError


class JWTValidator:
    def __init__(self, public_key_path: str, algorithm: str = "RS256",
                 issuer: str = "smartbarrel-auth"):
        self._public_key = Path(public_key_path).read_text()
        self._algorithm = algorithm
        self._issuer = issuer

    def decode(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "type"]},
            )
        except InvalidTokenError as e:
            raise ValueError(f"Invalid JWT: {e}") from e
        if payload.get("type") != "access":
            raise ValueError("Token type must be 'access'")
        return payload


def decode_token(token: str, public_key: str, algorithm: str = "RS256",
                 issuer: str = "smartbarrel-auth") -> dict[str, Any]:
    return jwt.decode(
        token, public_key, algorithms=[algorithm], issuer=issuer,
        options={"require": ["exp", "iat", "sub", "type"]},
    )
