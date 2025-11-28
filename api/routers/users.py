"""
Lucky Red - 用戶路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List

from shared.database.connection import get_db_session
from shared.database.models import User
from api.utils.telegram_auth import get_tg_id_from_header

router = APIRouter()


class UserProfile(BaseModel):
    """用戶資料"""
    id: int
    tg_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    xp: int
    invite_code: Optional[str]
    invite_count: int
    
    class Config:
        from_attributes = True


class UserBalance(BaseModel):
    """用戶餘額"""
    usdt: float
    ton: float
    stars: int
    points: int


@router.get("/profile/{tg_id}", response_model=UserProfile)
async def get_user_profile(
    tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取用戶資料"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/balance/{tg_id}", response_model=UserBalance)
async def get_user_balance(
    tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取用戶餘額"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserBalance(
        usdt=float(user.balance_usdt or 0),
        ton=float(user.balance_ton or 0),
        stars=user.balance_stars or 0,
        points=user.balance_points or 0,
    )


@router.get("/me/balance", response_model=UserBalance)
async def get_my_balance(
    db: AsyncSession = Depends(get_db_session),
    tg_id: Optional[int] = Depends(get_tg_id_from_header)
):
    """獲取當前用戶餘額（從 initData 中獲取 tg_id）"""
    if not tg_id:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserBalance(
        usdt=float(user.balance_usdt or 0),
        ton=float(user.balance_ton or 0),
        stars=user.balance_stars or 0,
        points=user.balance_points or 0,
    )


# 管理后台用户列表API
@router.get("/list")
async def list_users(
    search: Optional[str] = Query(None, description="搜索关键词（用户名、Telegram ID）"),
    level: Optional[int] = Query(None, description="等级筛选"),
    is_banned: Optional[bool] = Query(None, description="封禁状态筛选"),
    min_balance_usdt: Optional[float] = Query(None, description="最小USDT余额"),
    max_balance_usdt: Optional[float] = Query(None, description="最大USDT余额"),
    created_from: Optional[str] = Query(None, description="注册开始时间（ISO格式）"),
    created_to: Optional[str] = Query(None, description="注册结束时间（ISO格式）"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """获取用户列表（管理后台，支持高级筛选）"""
    query = select(User)
    
    # 搜索功能
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_term),
                User.first_name.ilike(search_term),
                User.tg_id.cast(str).ilike(search_term)
            )
        )
    
    # 高级筛选
    if level is not None:
        query = query.where(User.level == level)
    
    if is_banned is not None:
        query = query.where(User.is_banned == is_banned)
    
    if min_balance_usdt is not None:
        query = query.where(User.balance_usdt >= min_balance_usdt)
    
    if max_balance_usdt is not None:
        query = query.where(User.balance_usdt <= max_balance_usdt)
    
    if created_from:
        try:
            from_date = datetime.fromisoformat(created_from.replace('Z', '+00:00'))
            query = query.where(User.created_at >= from_date)
        except:
            pass
    
    if created_to:
        try:
            to_date = datetime.fromisoformat(created_to.replace('Z', '+00:00'))
            query = query.where(User.created_at <= to_date)
        except:
            pass
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 获取用户列表
    query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "success": True,
        "data": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "users": [
                {
                    "id": user.id,
                    "telegram_id": user.tg_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "balance_usdt": float(user.balance_usdt or 0),
                    "balance_ton": float(user.balance_ton or 0),
                    "balance_stars": user.balance_stars or 0,
                    "balance_points": user.balance_points or 0,
                    "level": user.level or 0,
                    "is_banned": user.is_banned or False,
                    "is_admin": user.is_admin or False,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
                for user in users
            ]
        }
    }


@router.get("/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """获取用户详情（管理后台）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "data": {
            "id": user.id,
            "telegram_id": user.tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "balance_usdt": float(user.balance_usdt or 0),
            "balance_ton": float(user.balance_ton or 0),
            "balance_stars": user.balance_stars or 0,
            "balance_points": user.balance_points or 0,
            "level": user.level or 0,
            "is_banned": user.is_banned or False,
            "is_admin": user.is_admin or False,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }

