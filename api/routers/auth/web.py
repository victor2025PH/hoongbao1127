"""
Web认证API - Google OAuth和Wallet连接
用于H5/Web版本的登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from loguru import logger

from shared.database.connection import get_db_session
from api.services.identity_service import IdentityService
from api.utils.auth_utils import create_access_token, TokenResponse
from api.routers.auth import UserResponse

router = APIRouter(prefix="/web", tags=["Web Auth"])


class GoogleAuthRequest(BaseModel):
    """Google OAuth请求"""
    id_token: str  # Google ID Token
    email: Optional[EmailStr] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


class WalletAuthRequest(BaseModel):
    """Wallet连接请求"""
    address: str  # 钱包地址
    network: str = "TON"  # 网络类型
    signature: Optional[str] = None  # 签名（用于验证）
    message: Optional[str] = None  # 签名消息


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Google OAuth登录
    
    注意：这是一个简化版本，实际生产环境需要验证Google ID Token
    """
    try:
        # TODO: 验证Google ID Token
        # 这里应该调用Google API验证token
        # 目前使用Mock验证
        
        # 提取用户信息
        provider_data = {
            'email': request.email,
            'given_name': request.given_name,
            'family_name': request.family_name,
            'picture': request.picture,
            'id_token': request.id_token
        }
        
        # 使用email作为provider_user_id
        provider_user_id = request.email or request.id_token[:20]
        
        # 获取或创建用户
        user = await IdentityService.get_or_create_user_by_identity(
            db=db,
            provider='google',
            provider_user_id=provider_user_id,
            provider_data=provider_data
        )
        
        # 生成Token
        token = create_access_token(user.id)
        
        logger.info(f"Google auth successful: email={request.email}, user_id={user.id}")
        
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
    except Exception as e:
        logger.error(f"Google auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )


@router.post("/wallet", response_model=TokenResponse)
async def wallet_auth(
    request: WalletAuthRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Wallet连接登录
    
    注意：这是一个简化版本，实际生产环境需要验证钱包签名
    """
    try:
        # TODO: 验证钱包签名
        # 这里应该验证signature和message
        # 目前使用Mock验证
        
        provider_data = {
            'network': request.network,
            'signature': request.signature,
            'message': request.message
        }
        
        # 获取或创建用户
        user = await IdentityService.get_or_create_user_by_identity(
            db=db,
            provider='wallet',
            provider_user_id=request.address,
            provider_data=provider_data
        )
        
        # 如果用户还没有wallet_address，更新它
        if not user.wallet_address:
            user.wallet_address = request.address
            user.wallet_network = request.network
            await db.commit()
        
        # 生成Token
        token = create_access_token(user.id)
        
        logger.info(f"Wallet auth successful: address={request.address}, user_id={user.id}")
        
        return TokenResponse(
            access_token=token,
            user={
                "id": user.id,
                "uuid": user.uuid,
                "wallet_address": user.wallet_address,
                "wallet_network": user.wallet_network,
                "primary_platform": user.primary_platform,
            }
        )
    except Exception as e:
        logger.error(f"Wallet auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wallet authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_web(
    current_user: "User" = Depends(lambda: None)  # TODO: 实现JWT验证
):
    """
    获取当前Web用户信息
    
    注意：需要实现JWT验证中间件
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="JWT authentication not implemented yet"
    )

