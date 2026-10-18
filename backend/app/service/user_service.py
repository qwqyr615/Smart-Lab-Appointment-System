from operator import or_

from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.user import (
    PageResponse,
    PasswordUpdateRequest,
    UserCreateRequest,
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


"""管理员增删改查用户"""


def create_user(data: UserCreateRequest, db: Session):
    """新增用户"""
    exist = db.query(User).filter(User.username == data.username).first()
    if exist:
        raise BusinessException(message="账号已存在")

    user = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name,
        role=data.role,
        email=data.email,
        avatar=data.avatar,
        status=data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_user(user_id: int, data: UserUpdateRequest, db: Session):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    payload = data.model_dump(exclude_none=True)
    for filed, value in payload.items():
        setattr(user, filed, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def delete_user(user_id: int, current_user: User, db: Session):
    """删除用户"""
    if user_id == current_user.id:
        raise BusinessException(message="不能删除当前登录的账号")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    db.delete(user)
    db.commit()
