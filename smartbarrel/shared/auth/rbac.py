"""RBAC dependency injection for FastAPI services."""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import JWTValidator

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    email: str
    roles: list[str]
    permissions: list[str]

    def has_permission(self, required: str) -> bool:
        if "*:*" in self.permissions:
            return True
        if required in self.permissions:
            return True
        resource = required.split(":")[0]
        return f"{resource}:*" in self.permissions


def get_jwt_validator(request: Request) -> JWTValidator:
    validator = getattr(request.app.state, "jwt_validator", None)
    if validator is None:
        raise RuntimeError("JWTValidator not configured on app.state.jwt_validator")
    return validator


def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    validator: Annotated[JWTValidator, Depends(get_jwt_validator)],
) -> CurrentUser:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        payload = validator.decode(creds.credentials)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    return CurrentUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


def require_permission(permission: str):
    def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Missing permission: {permission}"
            )
        return user
    return checker
