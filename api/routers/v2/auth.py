"""
Lucky Red API v2 - 認證路由
包含 Magic Link 無密碼登入功能
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from loguru import logger

from shared.config.settings import get_settings
from shared.database.connection import get_db_session
from shared.database.models import User, MagicLinkToken

router = APIRouter(prefix="/api/v2/auth", tags=["認證-v2"])
settings = get_settings()
security = HTTPBearer(auto_error=False)


# ==================== Pydantic 模型 ====================

class MagicLinkRequest(BaseModel):
    """請求生成 Magic Link"""
    tg_id: int


class MagicLinkResponse(BaseModel):
    """Magic Link 響應"""
    success: bool
    message: str
    login_url: Optional[str] = None
    expires_in_seconds: int = 300


class MagicLinkVerifyRequest(BaseModel):
    """驗證 Magic Link"""
    token: str


class TokenResponse(BaseModel):
    """Token 響應"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """用戶響應"""
    id: int
    tg_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    level: int
    balance_usdt: float
    balance_ton: float
    balance_stars: int
    balance_points: int


# ==================== 工具函數 ====================

def create_access_token(
    user_id: int,
    tg_id: int,
    auth_type: str = "magic_link",
    expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    """
    創建 JWT 訪問令牌
    
    Returns:
        tuple: (token, expire_time)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    payload = {
        "sub": str(user_id),
        "tg_id": tg_id,
        "type": auth_type,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def generate_magic_token() -> str:
    """生成安全的 Magic Link 令牌"""
    return secrets.token_urlsafe(32)


# ==================== API 端點 ====================

@router.post("/magic-link/generate", response_model=MagicLinkResponse)
async def generate_magic_link(
    request: MagicLinkRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    生成 Magic Link 登入連結
    
    此端點通常由 Telegram Bot 調用，為用戶生成一次性登入連結
    """
    # 查找用戶
    result = await db.execute(
        select(User).where(User.tg_id == request.tg_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用戶已被封禁"
        )
    
    # 生成令牌
    token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # 存儲令牌
    magic_link = MagicLinkToken(
        user_id=user.id,
        tg_id=user.tg_id,
        token=token,
        expires_at=expires_at,
        ip_address=req.client.host if req.client else None,
    )
    db.add(magic_link)
    await db.commit()
    
    # 構建登入 URL
    web_domain = getattr(settings, 'WEB_DOMAIN', 'app.yoursite.com')
    login_url = f"https://{web_domain}/auth/magic?token={token}"
    
    logger.info(f"Magic link generated for user {user.tg_id}")
    
    return MagicLinkResponse(
        success=True,
        message="登入連結已生成，5分鐘內有效",
        login_url=login_url,
        expires_in_seconds=300,
    )


@router.post("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(
    request: MagicLinkVerifyRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    驗證 Magic Link 並創建會話
    
    用戶點擊 Magic Link 後，H5 前端調用此端點進行認證
    """
    # 查找令牌
    result = await db.execute(
        select(MagicLinkToken).where(
            MagicLinkToken.token == request.token,
            MagicLinkToken.is_used == False,
            MagicLinkToken.expires_at > datetime.utcnow()
        )
    )
    magic_link = result.scalar_one_or_none()
    
    if not magic_link:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="連結已失效或已被使用"
        )
    
    # 標記為已使用
    magic_link.is_used = True
    magic_link.used_at = datetime.utcnow()
    magic_link.ip_address = req.client.host if req.client else magic_link.ip_address
    magic_link.user_agent = req.headers.get("user-agent")
    
    # 獲取用戶
    user_result = await db.execute(
        select(User).where(User.id == magic_link.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用戶已被封禁"
        )
    
    await db.commit()
    
    # 生成會話令牌
    access_token, expire_time = create_access_token(
        user_id=user.id,
        tg_id=user.tg_id,
        auth_type="magic_link",
        expires_delta=timedelta(days=7)
    )
    
    expires_in = int((expire_time - datetime.utcnow()).total_seconds())
    
    logger.info(f"Magic link verified for user {user.tg_id}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user={
            "id": user.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "level": user.level,
            "balance_usdt": float(user.balance_usdt or 0),
            "balance_ton": float(user.balance_ton or 0),
            "balance_stars": user.balance_stars or 0,
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取當前認證用戶信息"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證令牌"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證令牌"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用戶已被封禁"
        )
    
    return UserResponse(
        id=user.id,
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        level=user.level,
        balance_usdt=float(user.balance_usdt or 0),
        balance_ton=float(user.balance_ton or 0),
        balance_stars=user.balance_stars or 0,
        balance_points=user.balance_points or 0,
    )


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """刷新訪問令牌"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證令牌"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        tg_id = int(payload.get("tg_id"))
        auth_type = payload.get("type", "unknown")
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證令牌"
        )
    
    # 驗證用戶存在
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在或已被封禁"
        )
    
    # 生成新令牌
    new_token, expire_time = create_access_token(
        user_id=user_id,
        tg_id=tg_id,
        auth_type=auth_type,
        expires_delta=timedelta(days=7)
    )
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": int((expire_time - datetime.utcnow()).total_seconds()),
    }
