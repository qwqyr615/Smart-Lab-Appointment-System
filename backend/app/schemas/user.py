from typing import Any

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int

    # 允许从任意对象（比如 SQLAlchemy 模型）直接创建这个 Pydantic 模型。
    # 对象->转换成json
    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(BaseModel):
    username: str
    password: str = "124"
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str = "student"
    status: int = 1


class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None
    status: int | None = None


class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str


class PageResponse(BaseModel):
    """分页返回的结果"""

    list: Any = []
    total: int = 0
