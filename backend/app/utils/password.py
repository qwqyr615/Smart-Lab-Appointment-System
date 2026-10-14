# 密码加密和验证密码

import bcrypt


def hash_password(password: str) -> str:
    """对密码加密"""
    return bcrypt.hashpw(password=password.encode("Utf-8"), salt=bcrypt.gensalt())


def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码的有效性"""
    return bcrypt.checkpw(
        password=password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )
