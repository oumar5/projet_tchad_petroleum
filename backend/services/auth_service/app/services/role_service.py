"""Role and permission management."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Permission, Role


class RoleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_roles(self) -> list[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        return list((await self.session.execute(stmt)).scalars())

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_role(self, name: str, description: str | None,
                          permission_codes: list[str]) -> Role:
        permissions = await self._fetch_permissions(permission_codes)
        role = Role(name=name, description=description, permissions=permissions)
        self.session.add(role)
        await self.session.flush()
        return role

    async def list_permissions(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.resource, Permission.action)
        return list((await self.session.execute(stmt)).scalars())

    async def _fetch_permissions(self, codes: list[str]) -> list[Permission]:
        if not codes:
            return []
        pairs = [tuple(c.split(":", 1)) for c in codes if ":" in c]
        if not pairs:
            return []
        stmt = select(Permission).where(
            (Permission.resource.in_([p[0] for p in pairs]))
            & (Permission.action.in_([p[1] for p in pairs]))
        )
        all_perms = list((await self.session.execute(stmt)).scalars())
        wanted = set(pairs)
        return [p for p in all_perms if (p.resource, p.action) in wanted]
