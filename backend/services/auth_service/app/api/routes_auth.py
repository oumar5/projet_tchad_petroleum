"""Public auth endpoints: register, login, refresh, logout, me, password reset."""
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from shared.auth import CurrentUser, get_current_user

from ..core.redis_client import (
    record_login_failure,
    reset_login_failures,
)
from ..core.security import (
    generate_mfa_secret,
    mfa_provisioning_uri,
    verify_mfa_code,
)
from ..core.settings import AuthSettings, get_settings
from ..schemas import (
    LoginRequest,
    MeResponse,
    MfaEnableResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from ..services.audit_service import AuditService
from ..services.token_service import TokenService
from ..services.user_service import UserService
from .deps import get_audit_service, get_token_service, get_user_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])

MAX_LOGIN_FAILURES = 5


@router.post("/register", response_model=MeResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
    settings: Annotated[AuthSettings, Depends(get_settings)],
) -> MeResponse:
    if await user_service.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    user = await user_service.create(
        email=body.email, password=body.password, full_name=body.full_name,
        bcrypt_rounds=settings.bcrypt_rounds,
    )
    await audit.log(
        event="user.registered", user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return MeResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        roles=[r.name for r in user.roles],
        permissions=UserService.collect_permissions(user),
        mfa_enabled=user.mfa_secret is not None,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> TokenResponse:
    failures = await record_login_failure(body.email)
    if failures > MAX_LOGIN_FAILURES:
        await audit.log(event="login.locked", metadata={"email": body.email})
        raise HTTPException(429, "Too many failed attempts. Try again later.")

    user = await user_service.verify_credentials(body.email, body.password)
    if user is None:
        await audit.log(event="login.failed", metadata={"email": body.email})
        raise HTTPException(401, "Invalid credentials")

    if user.mfa_secret:
        if not body.mfa_code:
            raise HTTPException(401, "MFA code required")
        if not verify_mfa_code(user.mfa_secret, body.mfa_code):
            await audit.log(event="login.mfa_failed", user_id=user.id)
            raise HTTPException(401, "Invalid MFA code")

    await reset_login_failures(body.email)
    access, refresh, ttl = token_service.issue_pair(user)
    await audit.log(
        event="login.success", user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=ttl)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    try:
        access, ttl = await token_service.refresh_access(body.refresh_token, user_service)
    except ValueError as e:
        raise HTTPException(401, str(e)) from e
    return TokenResponse(access_token=access, refresh_token=body.refresh_token, expires_in=ttl)


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshRequest,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> None:
    try:
        await token_service.revoke_refresh(body.refresh_token)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    await audit.log(event="logout")


@router.get("/me", response_model=MeResponse)
async def me(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> MeResponse:
    user = await user_service.get_by_id(UUID(current.id))
    if user is None:
        raise HTTPException(404, "User not found")
    return MeResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        roles=[r.name for r in user.roles],
        permissions=UserService.collect_permissions(user),
        mfa_enabled=user.mfa_secret is not None,
    )


@router.post("/password/reset", status_code=202)
async def password_reset_request(
    body: PasswordResetRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> dict:
    user = await user_service.get_by_email(body.email)
    if user is not None:
        from datetime import datetime, timedelta, timezone
        from hashlib import sha256

        from ..models import PasswordReset
        token = secrets.token_urlsafe(32)
        token_hash = sha256(token.encode()).hexdigest()
        reset = PasswordReset(
            user_id=user.id, token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        user_service.session.add(reset)
        await user_service.session.flush()
        await audit.log(event="password.reset_requested", user_id=user.id,
                        metadata={"token_id": str(reset.id)})
        # TODO: publish 'user.password_reset_requested' for notification-service
    return {"detail": "If the email exists, a reset link has been sent."}


@router.post("/password/confirm", status_code=204)
async def password_reset_confirm(
    body: PasswordResetConfirm,
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
    settings: Annotated[AuthSettings, Depends(get_settings)],
) -> None:
    from datetime import datetime, timezone
    from hashlib import sha256

    from sqlalchemy import select

    from ..models import PasswordReset
    token_hash = sha256(body.token.encode()).hexdigest()
    stmt = select(PasswordReset).where(
        PasswordReset.token_hash == token_hash,
        PasswordReset.used_at.is_(None),
        PasswordReset.expires_at > datetime.now(timezone.utc),
    )
    reset = (await user_service.session.execute(stmt)).scalar_one_or_none()
    if reset is None:
        raise HTTPException(400, "Invalid or expired token")
    user = await user_service.get_by_id(reset.user_id)
    if user is None:
        raise HTTPException(400, "User not found")
    await user_service.update_password(user, body.new_password, settings.bcrypt_rounds)
    reset.used_at = datetime.now(timezone.utc)
    await audit.log(event="password.reset_completed", user_id=user.id)


@router.post("/mfa/enable", response_model=MfaEnableResponse)
async def mfa_enable(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> MfaEnableResponse:
    user = await user_service.get_by_id(UUID(current.id))
    if user is None:
        raise HTTPException(404, "User not found")
    if user.mfa_secret:
        raise HTTPException(409, "MFA already enabled")

    secret = generate_mfa_secret()
    user.mfa_secret = secret

    from hashlib import sha256

    from ..models import MfaRecoveryCode
    plain_codes = [secrets.token_hex(8) for _ in range(10)]
    for code in plain_codes:
        user_service.session.add(MfaRecoveryCode(
            user_id=user.id, code_hash=sha256(code.encode()).hexdigest(),
        ))
    await user_service.session.flush()
    await audit.log(event="mfa.enabled", user_id=user.id)

    return MfaEnableResponse(
        secret=secret,
        provisioning_uri=mfa_provisioning_uri(secret, user.email),
        recovery_codes=plain_codes,
    )
