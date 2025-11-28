"""
認證授權工具
JWT + RBAC
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database.connection import get_db_session
from shared.database.models import AdminUser, Role
from shared.config.settings import get_settings

settings = get_settings()

# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT 配置
SECRET_KEY = getattr(settings, "JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小時

# 调试：确保 JWT_SECRET 被正确加载
import logging
logger = logging.getLogger(__name__)
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    logger.warning("⚠️ JWT_SECRET 未设置或使用默认值，这可能导致 Token 验证失败")
else:
    logger.info(f"✅ JWT_SECRET 已加载 (长度: {len(SECRET_KEY)})")

# HTTP Bearer 認證
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼（支持 bcrypt 和 SHA256）"""
    # 先嘗試 bcrypt
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except:
        pass
    
    # 如果 bcrypt 失敗，嘗試 SHA256（用於測試）
    import hashlib
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    if hashed_password == sha256_hash:
        return True
    
    return False


def get_password_hash(password: str) -> str:
    """獲取密碼哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """創建訪問令牌"""
    to_encode = data.copy()
    # 确保 sub 是字符串（JWT 标准要求）
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> AdminUser:
    """獲取當前管理員用戶"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # sub 在 JWT 中是字符串，需要转换为整数
        admin_id_str = payload.get("sub")
        if admin_id_str is None:
            raise credentials_exception
        admin_id: int = int(admin_id_str)
    except (JWTError, ValueError, TypeError) as e:
        logger.error(f"JWT 验证失败: {str(e)}")
        logger.error(f"Token payload: {payload if 'payload' in locals() else 'N/A'}")
        raise credentials_exception
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    
    if admin is None:
        raise credentials_exception
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin user"
        )
    
    return admin


async def get_current_active_admin(
    current_admin: AdminUser = Depends(get_current_admin)
) -> AdminUser:
    """獲取當前活躍的管理員"""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin user"
        )
    return current_admin


def check_permission(admin: AdminUser, permission: str) -> bool:
    """檢查權限"""
    if not admin.role:
        return False
    
    permissions = admin.role.permissions or []
    return permission in permissions or "admin:*" in permissions

