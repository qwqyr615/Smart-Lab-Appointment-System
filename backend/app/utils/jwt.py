# 创建和解析JWT
from datetime import datetime, timedelta
import jwt
from app.config import settings


def create_access_token(user_id: int) -> str:
    """创建JWT token"""
    # 过期时间
    expire = datetime.now() + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    payload = {"user_id": user_id, "exp": expire}

    return jwt.encode(
        payload=payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_tolen(token: str) -> bool:
    """解析JWT token"""
    return jwt.decode(
        jwt=token, key=settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM
    )
