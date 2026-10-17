from collections import UserString

from fastapi import APIRouter, Depends
from app.common.response import Response
from app.schemas.auth import LoginRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordUpdateRequest, UserUpdateRequest
from app.service import user_service
from app.utils.password import verify_password
from app.utils.jwt import create_access_token
from app.dependencies.auth import get_current_user
from app.service.user_service import get_user_info

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
