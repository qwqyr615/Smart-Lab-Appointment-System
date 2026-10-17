from operator import or_

from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.user import (
    PageResponse,
    PasswordUpdateRequest,
    UserResponse,
    UserUpdateRequest,
)
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


def get_user_page_list(
    page: int, page_size: int, db: Session, keywords: str | None = None
):
    query = db.query(User)
    if keywords:
        query = query.filter(
            or_(User.username.ilike(f"%{keywords}%"), User.name.ilike(f"%{keywords}%"))
        )
    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items], total=total
    )
