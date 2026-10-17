from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.common.response import Response
from sqlalchemy.orm import Session


def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def update_user_info(data: UserUpdateRequest, user: User, db: Session):
    user_dict = data.model_dump(exclude_none=True)  # pydatic对象转换成字典,
    for field, value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
