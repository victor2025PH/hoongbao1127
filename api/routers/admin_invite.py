"""
邀请管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from shared.database.connection import get_db_session
from shared.database.models import User, Transaction
from api.utils.auth import get_current_active_admin, AdminUser
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/invite", tags=["管理后台-邀请管理"])


class InviteRelationItem(BaseModel):
    user_id: int
    user_tg_id: Optional[int] = None
    user_username: Optional[str] = None
    user_name: Optional[str] = None
    invite_code: Optional[str] = None
    invite_count: int
    invite_earnings: Decimal
    invited_by_tg_id: Optional[int] = None
    invited_by_username: Optional[str] = None
    invited_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InviteTreeItem(BaseModel):
    user: InviteRelationItem
    children: List['InviteTreeItem'] = []


class InviteStats(BaseModel):
    total_invites: int
    total_earnings: Decimal
    active_inviters: int
    average_invites: float
    top_inviter: Optional[dict] = None


@router.get("/list", response_model=dict)
async def list_invite_relations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    inviter_id: Optional[int] = Query(None),
    invitee_id: Optional[int] = Query(None),
    min_invites: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取邀请关系列表"""
    query = select(User)
    
    conditions = []
    
    if inviter_id:
        # 查找某个用户的邀请人
        inviter = await db.scalar(select(User).where(User.id == inviter_id))
        if inviter and inviter.invited_by:
            conditions.append(User.tg_id == inviter.invited_by)
        else:
            # 如果没有邀请人，返回空结果
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    if invitee_id:
        # 查找某个用户邀请的所有人
        inviter = await db.scalar(select(User).where(User.id == invitee_id))
        if inviter:
            conditions.append(User.invited_by == inviter.tg_id)
    
    if min_invites is not None:
        conditions.append(User.invite_count >= min_invites)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(User)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # 分页查询
    query = query.order_by(User.invite_count.desc(), User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 获取邀请人信息
    inviter_tg_ids = list(set(u.invited_by for u in users if u.invited_by))
    inviters_query = select(User).where(User.tg_id.in_(inviter_tg_ids))
    inviters_result = await db.execute(inviters_query)
    inviters = {inviter.tg_id: inviter for inviter in inviters_result.scalars().all()}
    
    # 构建响应数据
    items = []
    for user in users:
        inviter = inviters.get(user.invited_by) if user.invited_by else None
        items.append(InviteRelationItem(
            user_id=user.id,
            user_tg_id=user.tg_id,
            user_username=user.username,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            invite_code=user.invite_code,
            invite_count=user.invite_count or 0,
            invite_earnings=user.invite_earnings or Decimal(0),
            invited_by_tg_id=user.invited_by,
            invited_by_username=inviter.username if inviter else None,
            invited_by_name=f"{inviter.first_name or ''} {inviter.last_name or ''}".strip() if inviter else None,
            created_at=user.created_at,
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/tree/{user_id}")
async def get_invite_tree(
    user_id: int,
    depth: int = Query(3, ge=1, le=5),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取邀请关系树"""
    async def build_tree(uid: int, current_depth: int) -> Optional[InviteTreeItem]:
        if current_depth > depth:
            return None
        
        user_result = await db.execute(select(User).where(User.id == uid))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None
        
        # 获取邀请人信息
        inviter = None
        if user.invited_by:
            inviter_result = await db.execute(select(User).where(User.tg_id == user.invited_by))
            inviter = inviter_result.scalar_one_or_none()
        
        user_item = InviteRelationItem(
            user_id=user.id,
            user_tg_id=user.tg_id,
            user_username=user.username,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            invite_code=user.invite_code,
            invite_count=user.invite_count or 0,
            invite_earnings=user.invite_earnings or Decimal(0),
            invited_by_tg_id=user.invited_by,
            invited_by_username=inviter.username if inviter else None,
            invited_by_name=f"{inviter.first_name or ''} {inviter.last_name or ''}".strip() if inviter else None,
            created_at=user.created_at,
        )
        
        # 获取被邀请人
        invitees_result = await db.execute(
            select(User).where(User.invited_by == user.tg_id)
        )
        invitees = invitees_result.scalars().all()
        
        children = []
        for invitee in invitees:
            child_tree = await build_tree(invitee.id, current_depth + 1)
            if child_tree:
                children.append(child_tree)
        
        return InviteTreeItem(user=user_item, children=children)
    
    tree = await build_tree(user_id, 1)
    
    if not tree:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return tree


@router.get("/stats", response_model=InviteStats)
async def get_invite_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取邀请统计"""
    query = select(User).where(User.invite_count > 0)
    
    if start_date:
        query = query.where(User.created_at >= start_date)
    if end_date:
        query = query.where(User.created_at <= end_date)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    total_invites = sum(u.invite_count or 0 for u in users)
    total_earnings = sum(u.invite_earnings or Decimal(0) for u in users)
    active_inviters = len(users)
    average_invites = total_invites / active_inviters if active_inviters > 0 else 0
    
    # 找出邀请最多的用户
    top_inviter = None
    if users:
        top_user = max(users, key=lambda u: u.invite_count or 0)
        top_inviter = {
            "user_id": top_user.id,
            "user_tg_id": top_user.tg_id,
            "user_username": top_user.username,
            "user_name": f"{top_user.first_name or ''} {top_user.last_name or ''}".strip(),
            "invite_count": top_user.invite_count or 0,
            "invite_earnings": float(top_user.invite_earnings or 0),
        }
    
    return InviteStats(
        total_invites=total_invites,
        total_earnings=total_earnings,
        active_inviters=active_inviters,
        average_invites=round(average_invites, 2),
        top_inviter=top_inviter,
    )


@router.get("/trend")
async def get_invite_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin),
):
    """获取邀请趋势数据"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 按日期统计新注册用户（通过邀请）
    query = select(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('new_users'),
    ).where(
        User.created_at >= start_date,
        User.created_at <= end_date,
        User.invited_by.isnot(None),
    ).group_by(
        func.date(User.created_at)
    ).order_by(
        func.date(User.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    dates = []
    new_users = []
    
    for row in rows:
        dates.append(row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date))
        new_users.append(row.new_users)
    
    return {
        "dates": dates,
        "new_users": new_users,
    }

