"""
红包管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from shared.database.connection import get_db_session
from shared.database.models import RedPacket, RedPacketClaim, User, RedPacketStatus, RedPacketType, CurrencyType
from api.utils.auth import get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/redpackets", tags=["管理后台-红包管理"])


# Pydantic 模型
class RedPacketListItem(BaseModel):
    id: int
    uuid: str
    sender_id: int
    sender_tg_id: Optional[int] = None
    sender_username: Optional[str] = None
    sender_name: Optional[str] = None
    chat_id: Optional[int] = None
    chat_title: Optional[str] = None
    currency: str
    packet_type: str
    total_amount: Decimal
    total_count: int
    claimed_amount: Decimal
    claimed_count: int
    status: str
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RedPacketDetail(RedPacketListItem):
    claims: List[dict] = []


class RedPacketClaimItem(BaseModel):
    id: int
    user_id: int
    user_tg_id: Optional[int] = None
    user_username: Optional[str] = None
    user_name: Optional[str] = None
    amount: Decimal
    is_luckiest: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RedPacketStats(BaseModel):
    total_count: int
    total_amount: Decimal
    claimed_amount: Decimal
    average_amount: Decimal
    claim_rate: float
    active_count: int
    completed_count: int
    expired_count: int
    refunded_count: int


@router.get("/list", response_model=dict)
async def list_redpackets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    packet_type: Optional[str] = Query(None),
    sender_id: Optional[int] = Query(None),
    chat_id: Optional[int] = Query(None),
    uuid: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取红包列表"""
    query = select(RedPacket).options(selectinload(RedPacket.sender))
    
    # 构建筛选条件
    conditions = []
    
    if status:
        try:
            status_enum = RedPacketStatus(status)
            conditions.append(RedPacket.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")
    
    if currency:
        try:
            currency_enum = CurrencyType(currency)
            conditions.append(RedPacket.currency == currency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的币种: {currency}")
    
    if packet_type:
        try:
            type_enum = RedPacketType(packet_type)
            conditions.append(RedPacket.packet_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的红包类型: {packet_type}")
    
    if sender_id:
        conditions.append(RedPacket.sender_id == sender_id)
    
    if chat_id:
        conditions.append(RedPacket.chat_id == chat_id)
    
    if uuid:
        conditions.append(RedPacket.uuid.contains(uuid))
    
    if start_date:
        conditions.append(RedPacket.created_at >= start_date)
    
    if end_date:
        conditions.append(RedPacket.created_at <= end_date)
    
    if min_amount:
        conditions.append(RedPacket.total_amount >= min_amount)
    
    if max_amount:
        conditions.append(RedPacket.total_amount <= max_amount)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 获取总数
    count_query = select(func.count()).select_from(RedPacket)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # 分页查询
    query = query.order_by(RedPacket.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    redpackets = result.scalars().all()
    
    # 构建响应数据
    items = []
    for rp in redpackets:
        sender = rp.sender
        items.append(RedPacketListItem(
            id=rp.id,
            uuid=rp.uuid,
            sender_id=rp.sender_id,
            sender_tg_id=sender.tg_id if sender else None,
            sender_username=sender.username if sender else None,
            sender_name=f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else None,
            chat_id=rp.chat_id,
            chat_title=rp.chat_title,
            currency=rp.currency.value,
            packet_type=rp.packet_type.value,
            total_amount=rp.total_amount,
            total_count=rp.total_count,
            claimed_amount=rp.claimed_amount,
            claimed_count=rp.claimed_count,
            status=rp.status.value,
            message=rp.message,
            expires_at=rp.expires_at,
            created_at=rp.created_at,
            completed_at=rp.completed_at,
        ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{redpacket_id}", response_model=RedPacketDetail)
async def get_redpacket_detail(
    redpacket_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取红包详情"""
    query = select(RedPacket).options(
        selectinload(RedPacket.sender),
        selectinload(RedPacket.claims).selectinload(RedPacketClaim.user)
    ).where(RedPacket.id == redpacket_id)
    
    result = await db.execute(query)
    redpacket = result.scalar_one_or_none()
    
    if not redpacket:
        raise HTTPException(status_code=404, detail="红包不存在")
    
    sender = redpacket.sender
    claims = []
    for claim in redpacket.claims:
        user = claim.user
        claims.append({
            "id": claim.id,
            "user_id": claim.user_id,
            "user_tg_id": user.tg_id if user else None,
            "user_username": user.username if user else None,
            "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            "amount": float(claim.amount),
            "is_luckiest": claim.is_luckiest,
            "created_at": claim.claimed_at.isoformat() if hasattr(claim, 'claimed_at') and claim.claimed_at else None,
        })
    
    return RedPacketDetail(
        id=redpacket.id,
        uuid=redpacket.uuid,
        sender_id=redpacket.sender_id,
        sender_tg_id=sender.tg_id if sender else None,
        sender_username=sender.username if sender else None,
        sender_name=f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else None,
        chat_id=redpacket.chat_id,
        chat_title=redpacket.chat_title,
        currency=redpacket.currency.value,
        packet_type=redpacket.packet_type.value,
        total_amount=redpacket.total_amount,
        total_count=redpacket.total_count,
        claimed_amount=redpacket.claimed_amount,
        claimed_count=redpacket.claimed_count,
        status=redpacket.status.value,
        message=redpacket.message,
        expires_at=redpacket.expires_at,
        created_at=redpacket.created_at,
        completed_at=redpacket.completed_at,
        claims=claims,
    )


@router.post("/{redpacket_id}/refund")
async def refund_redpacket(
    redpacket_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """手动退款红包"""
    query = select(RedPacket).where(RedPacket.id == redpacket_id)
    result = await db.execute(query)
    redpacket = result.scalar_one_or_none()
    
    if not redpacket:
        raise HTTPException(status_code=404, detail="红包不存在")
    
    if redpacket.status == RedPacketStatus.REFUNDED:
        raise HTTPException(status_code=400, detail="红包已退款")
    
    if redpacket.status == RedPacketStatus.COMPLETED and redpacket.claimed_count > 0:
        raise HTTPException(status_code=400, detail="红包已被领取，无法退款")
    
    # 更新状态
    redpacket.status = RedPacketStatus.REFUNDED
    
    # 如果已领取，需要退还金额（这里简化处理，实际应该创建退款交易记录）
    # TODO: 实现退款逻辑，退还金额到发送者账户
    
    await db.commit()
    await db.refresh(redpacket)
    
    return {"success": True, "message": "退款成功"}


@router.post("/{redpacket_id}/extend")
async def extend_redpacket(
    redpacket_id: int,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """延长红包过期时间"""
    query = select(RedPacket).where(RedPacket.id == redpacket_id)
    result = await db.execute(query)
    redpacket = result.scalar_one_or_none()
    
    if not redpacket:
        raise HTTPException(status_code=404, detail="红包不存在")
    
    if redpacket.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="只能延长进行中的红包")
    
    if redpacket.expires_at:
        redpacket.expires_at = redpacket.expires_at + timedelta(hours=hours)
    else:
        redpacket.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    await db.commit()
    await db.refresh(redpacket)
    
    return {"success": True, "message": f"已延长 {hours} 小时", "new_expires_at": redpacket.expires_at}


@router.post("/{redpacket_id}/complete")
async def complete_redpacket(
    redpacket_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """强制完成红包"""
    query = select(RedPacket).where(RedPacket.id == redpacket_id)
    result = await db.execute(query)
    redpacket = result.scalar_one_or_none()
    
    if not redpacket:
        raise HTTPException(status_code=404, detail="红包不存在")
    
    if redpacket.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="只能完成进行中的红包")
    
    redpacket.status = RedPacketStatus.COMPLETED
    redpacket.completed_at = datetime.utcnow()
    
    # 如果未领取完，剩余金额需要处理（这里简化，实际应该退还）
    # TODO: 实现剩余金额退还逻辑
    
    await db.commit()
    await db.refresh(redpacket)
    
    return {"success": True, "message": "红包已强制完成"}


@router.delete("/{redpacket_id}")
async def delete_redpacket(
    redpacket_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """删除红包（软删除，实际应该标记删除）"""
    query = select(RedPacket).where(RedPacket.id == redpacket_id)
    result = await db.execute(query)
    redpacket = result.scalar_one_or_none()
    
    if not redpacket:
        raise HTTPException(status_code=404, detail="红包不存在")
    
    # 注意：这里直接删除，实际应该软删除
    # TODO: 添加 deleted_at 字段实现软删除
    await db.delete(redpacket)
    await db.commit()
    
    return {"success": True, "message": "红包已删除"}


@router.get("/stats/overview", response_model=RedPacketStats)
async def get_redpacket_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取红包统计概览"""
    query = select(RedPacket)
    
    if start_date or end_date:
        conditions = []
        if start_date:
            conditions.append(RedPacket.created_at >= start_date)
        if end_date:
            conditions.append(RedPacket.created_at <= end_date)
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    redpackets = result.scalars().all()
    
    total_count = len(redpackets)
    total_amount = sum(float(rp.total_amount) for rp in redpackets)
    claimed_amount = sum(float(rp.claimed_amount) for rp in redpackets)
    average_amount = total_amount / total_count if total_count > 0 else 0
    claim_rate = (claimed_amount / total_amount * 100) if total_amount > 0 else 0
    
    active_count = sum(1 for rp in redpackets if rp.status == RedPacketStatus.ACTIVE)
    completed_count = sum(1 for rp in redpackets if rp.status == RedPacketStatus.COMPLETED)
    expired_count = sum(1 for rp in redpackets if rp.status == RedPacketStatus.EXPIRED)
    refunded_count = sum(1 for rp in redpackets if rp.status == RedPacketStatus.REFUNDED)
    
    return RedPacketStats(
        total_count=total_count,
        total_amount=Decimal(str(total_amount)),
        claimed_amount=Decimal(str(claimed_amount)),
        average_amount=Decimal(str(average_amount)),
        claim_rate=round(claim_rate, 2),
        active_count=active_count,
        completed_count=completed_count,
        expired_count=expired_count,
        refunded_count=refunded_count,
    )


@router.get("/stats/trend")
async def get_redpacket_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session),
    current_admin: dict = Depends(get_current_admin),
):
    """获取红包趋势数据"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 按日期分组统计
    query = select(
        func.date(RedPacket.created_at).label('date'),
        func.count(RedPacket.id).label('count'),
        func.sum(RedPacket.total_amount).label('total_amount'),
        func.sum(RedPacket.claimed_amount).label('claimed_amount'),
    ).where(
        RedPacket.created_at >= start_date,
        RedPacket.created_at <= end_date,
    ).group_by(
        func.date(RedPacket.created_at)
    ).order_by(
        func.date(RedPacket.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    dates = []
    counts = []
    amounts = []
    claimed_amounts = []
    
    for row in rows:
        dates.append(row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date))
        counts.append(row.count)
        amounts.append(float(row.total_amount) if row.total_amount else 0)
        claimed_amounts.append(float(row.claimed_amount) if row.claimed_amount else 0)
    
    return {
        "dates": dates,
        "counts": counts,
        "amounts": amounts,
        "claimed_amounts": claimed_amounts,
    }

