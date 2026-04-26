from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str
    role_names: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[str]


class UserRolesUpdate(BaseModel):
    role_names: list[str]


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: list[str]


class PermissionResponse(BaseModel):
    id: UUID
    resource: str
    action: str
    description: str | None
