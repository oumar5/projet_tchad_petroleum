"""FastAPI dependencies for auth-service."""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.settings import AuthSettings, get_settings
from ..services.audit_service import AuditService
from ..services.role_service import RoleService
from ..services.token_service import TokenService
from ..services.user_service import UserService


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


async def get_db(
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncGenerator[AsyncSession, None]:
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_user_service(session: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(session)


def get_role_service(session: Annotated[AsyncSession, Depends(get_db)]) -> RoleService:
    return RoleService(session)


def get_audit_service(session: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    return AuditService(session)


def get_token_service(settings: Annotated[AuthSettings, Depends(get_settings)]) -> TokenService:
    return TokenService(settings)
