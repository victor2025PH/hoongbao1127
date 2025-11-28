"""
签到管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from shared.database.connection import get_async_db
from shared.database.models import CheckinRecord, User
from api.utils.auth import get_current_active_admin, AdminUser
from pydantic import BaseModel

router = APIRouter(prefix="/v1/admin/checkin", tags=["Admin - Checkin"])


class CheckinListItem(BaseModel):
    id: int
    user_id: int
    user_tg_id: Optional[int] = None
    user_username: Optional[str] = None
    user_name: Optional[str] = None
    checkin_date: datetime
    day_of_streak: int
    reward_points: int
    created_at: datetime

    class Config:
        from_attributes = True


class CheckinStats(BaseModel):
    total_checkins: int
    today_checkins: int
    total_rewards: int
    average_streak: float
    top_streak: int
    active_users: int


@router.get("/list", response_model=dict)
async def list_checkins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取签到列表"""
    query = select(CheckinRecord)
    
    conditions = []
    
    if user_id:
        conditions.append(CheckinRecord.user_id == user_id)
    
    if start_date:
        conditions.append(CheckinRecord.checkin_date >= start_date)
    
    if end_date:
        conditions.append(CheckinRecord.checkin_date <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(CheckinRecord)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # 分页查询
    query = query.order_by(CheckinRecord.checkin_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    checkins = result.scalars().all()
    
    # 获取用户信息
    user_ids = list(set(c.user_id for c in checkins))
    users_query = select(User).where(User.id.in_(user_ids))
    users_result = await db.execute(users_query)
    users = {user.id: user for user in users_result.scalars().all()}
    
    # 构建响应数据
    items = []
    for c in checkins:
        user = users.get(c.user_id)
        items.append(CheckinListItem(
            id=c.id,
            user_id=c.user_id,
            user_tg_id=user.tg_id if user else None,
            user_username=user.username if user else None,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            checkin_date=c.checkin_date,
            day_of_streak=c.day_of_streak,
            reward_points=c.reward_points,
            created_at=c.created_at,
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stats", response_model=CheckinStats)
async def get_checkin_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取签到统计"""
    query = select(CheckinRecord)
    
    if start_date or end_date:
        conditions = []
        if start_date:
            conditions.append(CheckinRecord.checkin_date >= start_date)
        if end_date:
            conditions.append(CheckinRecord.checkin_date <= end_date)
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    checkins = result.scalars().all()
    
    total_checkins = len(checkins)
    today = datetime.utcnow().date()
    today_checkins = sum(1 for c in checkins if c.checkin_date.date() == today)
    total_rewards = sum(c.reward_points for c in checkins)
    
    # 获取用户平均连续签到
    user_streaks_query = select(
        User.id,
        User.checkin_streak
    ).where(User.checkin_streak > 0)
    user_streaks_result = await db.execute(user_streaks_query)
    user_streaks = [row.checkin_streak for row in user_streaks_result.all()]
    
    average_streak = sum(user_streaks) / len(user_streaks) if user_streaks else 0
    top_streak = max(user_streaks) if user_streaks else 0
    
    # 活跃用户（有签到记录的用户）
    active_users_query = select(func.count(func.distinct(CheckinRecord.user_id)))
    if start_date or end_date:
        if start_date:
            active_users_query = active_users_query.where(CheckinRecord.checkin_date >= start_date)
        if end_date:
            active_users_query = active_users_query.where(CheckinRecord.checkin_date <= end_date)
    active_users = await db.scalar(active_users_query) or 0
    
    return CheckinStats(
        total_checkins=total_checkins,
        today_checkins=today_checkins,
        total_rewards=total_rewards,
        average_streak=round(average_streak, 2),
        top_streak=top_streak,
        active_users=active_users,
    )


@router.get("/trend")
async def get_checkin_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_async_db),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取签到趋势数据"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = select(
        func.date(CheckinRecord.checkin_date).label('date'),
        func.count(CheckinRecord.id).label('count'),
        func.sum(CheckinRecord.reward_points).label('total_rewards'),
    ).where(
        CheckinRecord.checkin_date >= start_date,
        CheckinRecord.checkin_date <= end_date,
    ).group_by(
        func.date(CheckinRecord.checkin_date)
    ).order_by(
        func.date(CheckinRecord.checkin_date)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    dates = []
    counts = []
    rewards = []
    
    for row in rows:
        dates.append(row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date))
        counts.append(row.count)
        rewards.append(int(row.total_rewards) if row.total_rewards else 0)
    
    return {
        "dates": dates,
        "counts": counts,
        "rewards": rewards,
    }

