from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.user import PasswordUpdateRequest, UserResponse, UserUpdateRequest
from app.common.response import Response
from sqlalchemy.orm import Session

from app.utils.password import verify_password, hash_password


def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def update_user_info(data: UserUpdateRequest, user: User, db: Session):
    user_dict = data.model_dump(exclude_none=True)  # pydatic对象转换成字典,
    for field, value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_password(data: PasswordUpdateRequest, user: User, db: Session):
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误")
    if data.new_password == data.old_password:
        raise BusinessException(message="新密码不能与原密码相同")
    user.password = hash_password(data.new_password)
    db.commit()
