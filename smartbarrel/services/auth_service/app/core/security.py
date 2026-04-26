"""Password hashing, JWT issuance, MFA TOTP."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import jwt
import pyotp
from passlib.context import CryptContext

from .settings import AuthSettings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str, rounds: int = 12) -> str:
    return _pwd.hash(password, rounds=rounds)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd.verify(password, hashed)


def issue_token(*, subject: str, email: str, roles: list[str], permissions: list[str],
                token_type: str, ttl_seconds: int, settings: AuthSettings) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "type": token_type,
    }
    private_key = Path(settings.jwt_private_key_path).read_text()
    return jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)


def decode_refresh(token: str, settings: AuthSettings) -> dict:
    public_key = Path(settings.jwt_public_key_path).read_text()
    payload = jwt.decode(
        token, public_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "iat", "sub", "type", "jti"]},
    )
    if payload.get("type") != "refresh":
        raise ValueError("Token must be a refresh token")
    return payload


def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def verify_mfa_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def mfa_provisioning_uri(secret: str, email: str, issuer: str = "SmartBarrel") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)
