"""Admin endpoints for users, roles, permissions, audit log."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth import CurrentUser, require_permission

from ..core.settings import AuthSettings, get_settings
from ..models import AuditLog, Role, User
from ..schemas.admin import (
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    UserCreate,
    UserResponse,
    UserRolesUpdate,
)
from ..services.audit_service import AuditService
from ..services.role_service import RoleService
from ..services.user_service import UserService
from .deps import get_audit_service, get_db, get_role_service, get_user_service

router = APIRouter(prefix="/v1/auth", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: Annotated[CurrentUser, Depends(require_permission("users:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserResponse]:
    stmt = select(User).options(selectinload(User.roles)).order_by(User.email)
    users = list((await session.execute(stmt)).scalars())
    return [
        UserResponse(
            id=u.id, email=u.email, full_name=u.full_name,
            is_active=u.is_active, roles=[r.name for r in u.roles],
        ) for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    actor: Annotated[CurrentUser, Depends(require_permission("users:write"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
    settings: Annotated[AuthSettings, Depends(get_settings)],
) -> UserResponse:
    if await user_service.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    user = await user_service.create(
        email=body.email, password=body.password, full_name=body.full_name,
        bcrypt_rounds=settings.bcrypt_rounds, role_names=body.role_names,
    )
    await audit.log(
        event="user.created", user_id=UUID(actor.id),
        metadata={"target_user_id": str(user.id), "roles": body.role_names},
    )
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        is_active=user.is_active, roles=[r.name for r in user.roles],
    )


@router.patch("/users/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: UUID,
    body: UserRolesUpdate,
    actor: Annotated[CurrentUser, Depends(require_permission("users:write"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> UserResponse:
    user = await user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    stmt = select(Role).where(Role.name.in_(body.role_names))
    roles = list((await session.execute(stmt)).scalars())
    user.roles = roles
    await session.flush()
    await audit.log(
        event="user.roles_updated", user_id=UUID(actor.id),
        metadata={"target_user_id": str(user.id), "roles": body.role_names},
    )
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        is_active=user.is_active, roles=[r.name for r in user.roles],
    )


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    actor: Annotated[CurrentUser, Depends(require_permission("users:delete"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    user.is_active = False
    await audit.log(
        event="user.deactivated", user_id=UUID(actor.id),
        metadata={"target_user_id": str(user.id)},
    )


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    _: Annotated[CurrentUser, Depends(require_permission("roles:read"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
) -> list[RoleResponse]:
    roles = await role_service.list_roles()
    return [
        RoleResponse(
            id=r.id, name=r.name, description=r.description,
            permissions=[f"{p.resource}:{p.action}" for p in r.permissions],
        ) for r in roles
    ]


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    body: RoleCreate,
    actor: Annotated[CurrentUser, Depends(require_permission("roles:write"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> RoleResponse:
    if await role_service.get_by_name(body.name):
        raise HTTPException(409, "Role already exists")
    role = await role_service.create_role(body.name, body.description, body.permission_codes)
    await audit.log(
        event="role.created", user_id=UUID(actor.id),
        metadata={"role_id": str(role.id), "name": role.name},
    )
    return RoleResponse(
        id=role.id, name=role.name, description=role.description,
        permissions=[f"{p.resource}:{p.action}" for p in role.permissions],
    )


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    _: Annotated[CurrentUser, Depends(require_permission("roles:read"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
) -> list[PermissionResponse]:
    perms = await role_service.list_permissions()
    return [
        PermissionResponse(
            id=p.id, resource=p.resource, action=p.action, description=p.description,
        ) for p in perms
    ]


@router.get("/audit")
async def list_audit(
    _: Annotated[CurrentUser, Depends(require_permission("audit:read"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 50,
) -> dict:
    offset = (page - 1) * page_size
    stmt = (
        select(AuditLog).order_by(AuditLog.created_at.desc())
        .limit(page_size).offset(offset)
    )
    rows = list((await session.execute(stmt)).scalars())
    return {
        "items": [
            {
                "id": r.id,
                "user_id": str(r.user_id) if r.user_id else None,
                "event": r.event,
                "metadata": r.metadata_json,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat(),
            } for r in rows
        ],
        "page": page,
        "page_size": page_size,
    }
