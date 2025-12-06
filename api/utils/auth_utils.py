"""
认证工具函数
用于避免循环导入
"""
from datetime import datetime, timedelta
from jose import jwt
from shared.config.settings import get_settings
from pydantic import BaseModel

settings = get_settings()


def create_access_token(user_id: int) -> str:
    """創建 JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class TokenResponse(BaseModel):
    """Token 響應"""
    access_token: str
    token_type: str = "bearer"
    user: dict

