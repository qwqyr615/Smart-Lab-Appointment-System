from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: int
    username: str
    password: str
    role: str
    email: str | None = None
    phone: str | None = None
    status: int

    # 允许从任意对象（比如 SQLAlchemy 模型）直接创建这个 Pydantic 模型。
    # 对象->转换成json
    model_config = ConfigDict(from_attributes=True)
