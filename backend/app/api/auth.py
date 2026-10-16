from fastapi import APIRouter, Depends
from app.common.exceptions import BusinessException
from app.common.response import Response
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    result = auth_service.login(data, db)
    return Response.success(
        message="登录成功",
        data=result,
    )


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    auth_service.register(data, db)
    return Response.success(message="注册成功")
