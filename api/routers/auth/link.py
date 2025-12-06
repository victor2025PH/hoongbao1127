"""
Magic Link API - 跨平台账户链接
用于Telegram用户生成Web登录链接
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from datetime import datetime, timedelta
from shared.database.connection import get_db_session
from shared.database.models import User
from api.services.identity_service import IdentityService
from api.utils.telegram_auth import get_tg_id_from_header
from api.utils.auth_utils import create_access_token, TokenResponse
from shared.config.settings import get_settings

router = APIRouter(prefix="/link", tags=["Account Link"])
settings = get_settings()


class MagicLinkGenerateRequest(BaseModel):
    """生成Magic Link请求"""
    link_type: str = "magic_login"  # 'magic_login', 'wallet_link', 'cross_platform'
    expires_in_hours: int = 24


class MagicLinkResponse(BaseModel):
    """Magic Link响应"""
    token: str
    link_url: str
    expires_at: str


class MagicLinkVerifyRequest(BaseModel):
    """验证Magic Link请求"""
    token: str


@router.post("/magic-link/generate", response_model=MagicLinkResponse)
async def generate_magic_link(
    request: MagicLinkGenerateRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """
    生成Magic Link（Telegram用户生成Web登录链接）
    
    需要Telegram认证（通过X-Telegram-Init-Data header）
    """
    if not tg_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram authentication required"
        )
    
    # 获取用户
    user = await IdentityService.get_user_by_telegram_id(db, tg_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 生成Magic Link
    token = await IdentityService.generate_magic_link(
        db=db,
        user_id=user.id,
        link_type=request.link_type,
        expires_in_hours=request.expires_in_hours,
        metadata={
            'generated_by': 'telegram',
            'tg_id': tg_id
        }
    )
    
    # 构建完整URL（需要根据实际前端URL配置）
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://mini.usdt2026.cc')
    link_url = f"{frontend_url}/auth/magic-link?token={token}"
    
    logger.info(f"Generated magic link for user_id={user.id}, tg_id={tg_id}")
    
    return MagicLinkResponse(
        token=token,
        link_url=link_url,
        expires_at=(datetime.utcnow() + timedelta(hours=request.expires_in_hours)).isoformat()
    )


@router.post("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(
    request: MagicLinkVerifyRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    验证Magic Link并返回JWT Token
    
    用于Web端通过Magic Link登录
    """
    # 验证Magic Link
    user = await IdentityService.verify_magic_link(
        db=db,
        token=request.token,
        mark_used=True
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )
    
    # 生成Token
    token = create_access_token(user.id)
    
    logger.info(f"Magic link verified: user_id={user.id}")
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "uuid": user.uuid,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "primary_platform": user.primary_platform,
        }
    )


@router.get("/identities")
async def get_user_identities(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户的所有身份链接
    
    需要Telegram认证
    """
    if not tg_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram authentication required"
        )
    
    # 获取用户
    user = await IdentityService.get_user_by_telegram_id(db, tg_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 获取所有身份
    identities = await IdentityService.get_user_identities(db, user.id)
    
    return {
        "user_id": user.id,
        "identities": [
            {
                "id": identity.id,
                "provider": identity.provider,
                "provider_user_id": identity.provider_user_id,
                "is_primary": identity.is_primary,
                "verified_at": identity.verified_at.isoformat() if identity.verified_at else None,
                "created_at": identity.created_at.isoformat()
            }
            for identity in identities
        ]
    }

