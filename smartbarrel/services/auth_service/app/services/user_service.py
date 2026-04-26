"""Business logic for user management."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.security import hash_password, verify_password
from ..models import Permission, Role, User


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, email: str, password: str, full_name: str,
                     bcrypt_rounds: int = 12, role_names: list[str] | None = None) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password, rounds=bcrypt_rounds),
            full_name=full_name,
        )
        self.session.add(user)
        await self.session.flush()

        if role_names:
            await self._attach_roles(user, role_names)
        else:
            await self._attach_roles(user, ["viewer"])

        await self.session.flush()
        return await self.get_by_id(user.id)  # type: ignore[return-value]

    async def _attach_roles(self, user: User, role_names: list[str]) -> None:
        stmt = select(Role).where(Role.name.in_(role_names))
        roles = list((await self.session.execute(stmt)).scalars())
        user.roles = roles

    @staticmethod
    def collect_permissions(user: User) -> list[str]:
        codes: set[str] = set()
        for role in user.roles:
            for perm in role.permissions:
                codes.add(f"{perm.resource}:{perm.action}")
        return sorted(codes)

    async def verify_credentials(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def update_password(self, user: User, new_password: str,
                              bcrypt_rounds: int = 12) -> None:
        user.password_hash = hash_password(new_password, rounds=bcrypt_rounds)
        await self.session.flush()
