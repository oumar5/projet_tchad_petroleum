"""Token issuance, refresh and revocation."""
from ..core.redis_client import blocklist_jti, is_jti_blocklisted
from ..core.security import decode_refresh, issue_token
from ..core.settings import AuthSettings
from ..models import User
from .user_service import UserService


class TokenService:
    def __init__(self, settings: AuthSettings):
        self.settings = settings

    def issue_pair(self, user: User) -> tuple[str, str, int]:
        roles = [r.name for r in user.roles]
        permissions = UserService.collect_permissions(user)
        access = issue_token(
            subject=str(user.id),
            email=user.email,
            roles=roles,
            permissions=permissions,
            token_type="access",
            ttl_seconds=self.settings.jwt_access_ttl_seconds,
            settings=self.settings,
        )
        refresh = issue_token(
            subject=str(user.id),
            email=user.email,
            roles=roles,
            permissions=permissions,
            token_type="refresh",
            ttl_seconds=self.settings.jwt_refresh_ttl_seconds,
            settings=self.settings,
        )
        return access, refresh, self.settings.jwt_access_ttl_seconds

    async def refresh_access(self, refresh_token: str, user_service: UserService) -> tuple[str, int]:
        payload = decode_refresh(refresh_token, self.settings)
        jti = payload["jti"]
        if await is_jti_blocklisted(jti):
            raise ValueError("Refresh token revoked")
        from uuid import UUID
        user = await user_service.get_by_id(UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise ValueError("User inactive")
        access = issue_token(
            subject=str(user.id),
            email=user.email,
            roles=[r.name for r in user.roles],
            permissions=UserService.collect_permissions(user),
            token_type="access",
            ttl_seconds=self.settings.jwt_access_ttl_seconds,
            settings=self.settings,
        )
        return access, self.settings.jwt_access_ttl_seconds

    async def revoke_refresh(self, refresh_token: str) -> None:
        from datetime import datetime, timezone
        payload = decode_refresh(refresh_token, self.settings)
        ttl = max(0, payload["exp"] - int(datetime.now(timezone.utc).timestamp()))
        if ttl > 0:
            await blocklist_jti(payload["jti"], ttl)
