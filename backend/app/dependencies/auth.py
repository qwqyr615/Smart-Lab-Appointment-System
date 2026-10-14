from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_access_tolen

"""
验证用户是否登录（Token 是否有效）
确认用户是否存在（从数据库查询）
检查用户是否被禁用（状态检查）
返回当前登录用户的信息（供接口使用）
"""

"""
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
token: str=Depends(oauth2_scheme) 就会提取

Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
↓ oauth2_scheme
↓ token = "eyJhbGciOiJIUzI1NiIs..."
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """JWT token 鉴权验证合法性"""
    try:
        payload = decode_access_tolen(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录"
        )
    # 获取用户ID
    user_id = payload["user_id"]
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, deatil="无效的登录凭证"
        )
    # 从数据库根据用户ID查询用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户被禁用"
        )
    return user
