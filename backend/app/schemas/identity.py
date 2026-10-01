from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class IdentityInput(BaseModel):
    model_config = ConfigDict(extra='forbid')


class RefreshInput(IdentityInput):
    refresh_token: str = Field(min_length=20, max_length=4096)


class PasswordChange(IdentityInput):
    current_password: SecretStr
    new_password: SecretStr = Field(min_length=12, max_length=1024)


class ResetRequest(IdentityInput):
    username: str = Field(min_length=1, max_length=120)


class ResetConfirm(IdentityInput):
    token: str = Field(min_length=32, max_length=200)
    new_password: SecretStr = Field(min_length=12, max_length=1024)


class UserCreate(IdentityInput):
    username: str = Field(pattern=r'^[A-Za-z0-9_.@-]{1,120}$')
    password: SecretStr = Field(min_length=12, max_length=1024)
    scope_mode: Literal['restricted', 'global'] = 'restricted'


class UserUpdate(IdentityInput):
    active: bool | None = None
    mfa_required: bool | None = None
    scope_mode: Literal['restricted', 'global'] | None = None


class RoleCreate(IdentityInput):
    name: str = Field(pattern=r'^[a-z][a-z0-9_.-]{1,79}$')
    permission_ids: list[UUID] = Field(default_factory=list, max_length=100)
