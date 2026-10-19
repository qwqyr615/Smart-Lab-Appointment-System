from fastapi import APIRouter, Depends
from app.common.response import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordUpdateRequest, UserUpdateRequest, UserCreateRequest
from app.service import user_service
from app.dependencies.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return Response.success(data=user_service.get_user_info(current_user))


@router.put("/update")
def update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户信息"""
    return Response.success(data=user_service.update_user_info(data, current_user, db))


@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    user_service.update_password(data, user, db)
    return Response.success(message="密码修改成功")


@router.get("/list")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """分页模糊查询用户列表"""
    res = user_service.get_user_page_list(
        page=page, page_size=page_size, db=db, keywords=keywords
    )
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.create_user(data, db)
    return Response.success(data=res)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.update_user(user_id, data, db)
    return Response.success(data=res)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user_service.delete_user(user_id, current_user, db)
    return Response.success("用户删除成功")
