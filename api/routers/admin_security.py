"""
管理后台 - 安全中心路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from shared.database.connection import get_db_session
from shared.database.models import (
    User, SybilAlert, DeviceFingerprint, IPSession, 
    LedgerEntry, CurrencySource, WithdrawableStatus, RiskLevel
)
from api.utils.auth import get_current_active_admin, AdminUser

router = APIRouter(prefix="/api/v1/admin/security", tags=["管理后台-安全中心"])


# ============== 數據模型 ==============

class AlertActionRequest(BaseModel):
    action: str  # resolve, dismiss, escalate
    note: Optional[str] = None


class DeviceActionRequest(BaseModel):
    action: str  # block, unblock, trust
    reason: Optional[str] = None


class IPActionRequest(BaseModel):
    action: str  # block, unblock, whitelist
    reason: Optional[str] = None


class LiquidityAdjustRequest(BaseModel):
    user_id: int
    entry_id: int
    new_status: str  # locked, cooldown, withdrawable
    reason: str


# ============== 安全總覽 ==============

@router.get("/stats")
async def get_security_stats(
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取安全統計數據"""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    # 今日攔截請求數
    today_blocked = 0
    try:
        result = await db.execute(
            select(func.count(SybilAlert.id)).where(
                and_(
                    func.date(SybilAlert.created_at) == today,
                    SybilAlert.risk_level.in_(['high', 'critical'])
                )
            )
        )
        today_blocked = result.scalar() or 0
    except Exception:
        pass
    
    # 昨日攔截
    yesterday_blocked = 0
    try:
        result = await db.execute(
            select(func.count(SybilAlert.id)).where(
                and_(
                    func.date(SybilAlert.created_at) == yesterday,
                    SybilAlert.risk_level.in_(['high', 'critical'])
                )
            )
        )
        yesterday_blocked = result.scalar() or 0
    except Exception:
        pass
    
    # 可疑帳號數（24小時內多次觸發警報的用戶）
    suspicious_users = 0
    try:
        result = await db.execute(
            select(func.count(func.distinct(SybilAlert.user_id))).where(
                SybilAlert.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        )
        suspicious_users = result.scalar() or 0
    except Exception:
        pass
    
    # 待解鎖 Stars 餘額
    pending_stars = 0.0
    try:
        result = await db.execute(
            select(func.sum(LedgerEntry.amount)).where(
                and_(
                    LedgerEntry.currency_source == CurrencySource.STARS_CREDIT,
                    LedgerEntry.withdrawable_status.in_([
                        WithdrawableStatus.LOCKED, 
                        WithdrawableStatus.COOLDOWN
                    ])
                )
            )
        )
        pending_stars = float(result.scalar() or 0)
    except Exception:
        pass
    
    # 活躍設備數（24小時內）
    active_devices = 0
    try:
        result = await db.execute(
            select(func.count(DeviceFingerprint.id)).where(
                DeviceFingerprint.last_seen >= datetime.utcnow() - timedelta(hours=24)
            )
        )
        active_devices = result.scalar() or 0
    except Exception:
        pass
    
    # 可疑 IP 數（同 IP 多帳號）
    suspicious_ips = 0
    try:
        result = await db.execute(
            select(func.count(func.distinct(IPSession.ip_address))).where(
                IPSession.is_active == True
            ).group_by(IPSession.ip_address).having(
                func.count(func.distinct(IPSession.user_id)) > 3
            )
        )
        suspicious_ips = len(result.all())
    except Exception:
        pass
    
    # 未處理警報數
    pending_alerts = 0
    try:
        result = await db.execute(
            select(func.count(SybilAlert.id)).where(
                SybilAlert.resolved == False
            )
        )
        pending_alerts = result.scalar() or 0
    except Exception:
        pass
    
    return {
        "success": True,
        "data": {
            "today_blocked": today_blocked,
            "yesterday_blocked": yesterday_blocked,
            "blocked_change": today_blocked - yesterday_blocked,
            "suspicious_users": suspicious_users,
            "pending_stars": pending_stars,
            "active_devices": active_devices,
            "suspicious_ips": suspicious_ips,
            "pending_alerts": pending_alerts
        }
    }


@router.get("/trends")
async def get_security_trends(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取安全趨勢數據"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    # 攔截趨勢
    block_trends = []
    for date in date_list:
        try:
            result = await db.execute(
                select(func.count(SybilAlert.id)).where(
                    and_(
                        func.date(SybilAlert.created_at) == date,
                        SybilAlert.risk_level.in_(['high', 'critical'])
                    )
                )
            )
            count = result.scalar() or 0
        except Exception:
            count = 0
        block_trends.append({
            "date": date.isoformat(),
            "count": count
        })
    
    # 按攔截類型統計
    type_stats = []
    try:
        result = await db.execute(
            select(
                SybilAlert.alert_type,
                func.count(SybilAlert.id).label('count')
            ).where(
                SybilAlert.created_at >= datetime.utcnow() - timedelta(days=days)
            ).group_by(SybilAlert.alert_type)
        )
        for row in result:
            type_stats.append({
                "type": row.alert_type,
                "count": row.count
            })
    except Exception:
        pass
    
    return {
        "success": True,
        "data": {
            "block_trends": block_trends,
            "type_stats": type_stats
        }
    }


# ============== 風險監控 ==============

@router.get("/risk/users")
async def get_risk_users(
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取風險用戶列表"""
    # 基於警報記錄統計用戶風險
    query = select(
        SybilAlert.user_id,
        func.count(SybilAlert.id).label('alert_count'),
        func.max(SybilAlert.risk_level).label('max_risk'),
        func.max(SybilAlert.created_at).label('last_alert')
    ).group_by(SybilAlert.user_id)
    
    if risk_level:
        query = query.having(func.max(SybilAlert.risk_level) == risk_level)
    
    query = query.order_by(desc('alert_count')).offset((page - 1) * page_size).limit(page_size)
    
    try:
        result = await db.execute(query)
        rows = result.all()
    except Exception:
        rows = []
    
    users = []
    for row in rows:
        # 獲取用戶詳情
        user_result = await db.execute(
            select(User).where(User.id == row.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            users.append({
                "user_id": row.user_id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "alert_count": row.alert_count,
                "risk_level": row.max_risk,
                "last_alert": row.last_alert.isoformat() if row.last_alert else None,
                "balance": float(user.balance_usdt or 0),
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
    
    # 總數
    count_query = select(func.count(func.distinct(SybilAlert.user_id)))
    if risk_level:
        count_query = count_query.where(SybilAlert.risk_level == risk_level)
    
    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception:
        total = 0
    
    return {
        "success": True,
        "data": {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


# ============== 警報管理 ==============

@router.get("/alerts")
async def get_alerts(
    resolved: Optional[bool] = None,
    risk_level: Optional[str] = None,
    alert_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取警報列表"""
    query = select(SybilAlert)
    
    conditions = []
    if resolved is not None:
        conditions.append(SybilAlert.resolved == resolved)
    if risk_level:
        conditions.append(SybilAlert.risk_level == risk_level)
    if alert_type:
        conditions.append(SybilAlert.alert_type == alert_type)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(SybilAlert.created_at)).offset((page - 1) * page_size).limit(page_size)
    
    try:
        result = await db.execute(query)
        alerts = result.scalars().all()
    except Exception:
        alerts = []
    
    # 總數
    count_query = select(func.count(SybilAlert.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception:
        total = 0
    
    return {
        "success": True,
        "data": {
            "alerts": [
                {
                    "id": alert.id,
                    "user_id": alert.user_id,
                    "alert_type": alert.alert_type,
                    "risk_level": alert.risk_level,
                    "details": alert.details,
                    "ip_address": alert.ip_address,
                    "resolved": alert.resolved,
                    "resolved_by": alert.resolved_by,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None
                }
                for alert in alerts
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/alerts/{alert_id}/action")
async def handle_alert_action(
    alert_id: int,
    request: AlertActionRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """處理警報動作"""
    result = await db.execute(
        select(SybilAlert).where(SybilAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="警報不存在")
    
    if request.action == "resolve":
        alert.resolved = True
        alert.resolved_by = admin.id
        alert.resolved_at = datetime.utcnow()
    elif request.action == "dismiss":
        alert.resolved = True
        alert.resolved_by = admin.id
        alert.resolved_at = datetime.utcnow()
    elif request.action == "escalate":
        alert.risk_level = "critical"
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"警報已{request.action}"
    }


# ============== 設備管理 ==============

@router.get("/devices")
async def get_devices(
    user_id: Optional[int] = None,
    is_blocked: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取設備列表"""
    query = select(DeviceFingerprint)
    
    conditions = []
    if user_id:
        conditions.append(DeviceFingerprint.user_id == user_id)
    if is_blocked is not None:
        conditions.append(DeviceFingerprint.is_blocked == is_blocked)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(DeviceFingerprint.last_seen)).offset((page - 1) * page_size).limit(page_size)
    
    try:
        result = await db.execute(query)
        devices = result.scalars().all()
    except Exception:
        devices = []
    
    # 總數
    count_query = select(func.count(DeviceFingerprint.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception:
        total = 0
    
    return {
        "success": True,
        "data": {
            "devices": [
                {
                    "id": device.id,
                    "user_id": device.user_id,
                    "fingerprint": device.fingerprint[:16] + "..." if device.fingerprint else None,
                    "platform": device.platform,
                    "browser": device.browser,
                    "device_type": device.device_type,
                    "is_blocked": device.is_blocked,
                    "is_trusted": device.is_trusted,
                    "risk_score": device.risk_score,
                    "first_seen": device.first_seen.isoformat() if device.first_seen else None,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None
                }
                for device in devices
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/devices/{device_id}/action")
async def handle_device_action(
    device_id: int,
    request: DeviceActionRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """處理設備動作"""
    result = await db.execute(
        select(DeviceFingerprint).where(DeviceFingerprint.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="設備不存在")
    
    if request.action == "block":
        device.is_blocked = True
        device.is_trusted = False
    elif request.action == "unblock":
        device.is_blocked = False
    elif request.action == "trust":
        device.is_trusted = True
        device.is_blocked = False
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"設備已{request.action}"
    }


# ============== IP 監控 ==============

@router.get("/ip-sessions")
async def get_ip_sessions(
    ip_address: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取 IP 會話列表"""
    query = select(IPSession)
    
    conditions = []
    if ip_address:
        conditions.append(IPSession.ip_address.like(f"%{ip_address}%"))
    if is_active is not None:
        conditions.append(IPSession.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(IPSession.last_activity)).offset((page - 1) * page_size).limit(page_size)
    
    try:
        result = await db.execute(query)
        sessions = result.scalars().all()
    except Exception:
        sessions = []
    
    # 總數
    count_query = select(func.count(IPSession.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception:
        total = 0
    
    return {
        "success": True,
        "data": {
            "sessions": [
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "ip_address": session.ip_address,
                    "country": session.country,
                    "city": session.city,
                    "is_active": session.is_active,
                    "is_blocked": session.is_blocked,
                    "claim_count": session.claim_count,
                    "last_claim_at": session.last_claim_at.isoformat() if session.last_claim_at else None,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None
                }
                for session in sessions
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/ip-stats")
async def get_ip_stats(
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取 IP 統計"""
    # 同 IP 多用戶統計
    multi_user_ips = []
    try:
        result = await db.execute(
            select(
                IPSession.ip_address,
                func.count(func.distinct(IPSession.user_id)).label('user_count'),
                func.sum(IPSession.claim_count).label('total_claims')
            ).where(
                IPSession.is_active == True
            ).group_by(IPSession.ip_address).having(
                func.count(func.distinct(IPSession.user_id)) > 1
            ).order_by(desc('user_count')).limit(20)
        )
        for row in result:
            multi_user_ips.append({
                "ip_address": row.ip_address,
                "user_count": row.user_count,
                "total_claims": row.total_claims or 0
            })
    except Exception:
        pass
    
    # IP 地區分布
    region_stats = []
    try:
        result = await db.execute(
            select(
                IPSession.country,
                func.count(func.distinct(IPSession.user_id)).label('user_count')
            ).where(
                IPSession.country.isnot(None)
            ).group_by(IPSession.country).order_by(desc('user_count')).limit(10)
        )
        for row in result:
            region_stats.append({
                "country": row.country,
                "user_count": row.user_count
            })
    except Exception:
        pass
    
    return {
        "success": True,
        "data": {
            "multi_user_ips": multi_user_ips,
            "region_stats": region_stats
        }
    }


@router.post("/ip/{ip_address}/action")
async def handle_ip_action(
    ip_address: str,
    request: IPActionRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """處理 IP 動作"""
    result = await db.execute(
        select(IPSession).where(IPSession.ip_address == ip_address)
    )
    sessions = result.scalars().all()
    
    if not sessions:
        raise HTTPException(status_code=404, detail="IP 不存在")
    
    for session in sessions:
        if request.action == "block":
            session.is_blocked = True
        elif request.action == "unblock":
            session.is_blocked = False
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"IP {ip_address} 已{request.action}，影響 {len(sessions)} 個會話"
    }


# ============== 流動性管理 ==============

@router.get("/liquidity/stats")
async def get_liquidity_stats(
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取流動性統計"""
    stats = {
        "total_locked": 0,
        "total_cooldown": 0,
        "total_withdrawable": 0,
        "by_source": []
    }
    
    try:
        # 按狀態統計
        for status in [WithdrawableStatus.LOCKED, WithdrawableStatus.COOLDOWN, WithdrawableStatus.WITHDRAWABLE]:
            result = await db.execute(
                select(func.sum(LedgerEntry.amount)).where(
                    LedgerEntry.withdrawable_status == status
                )
            )
            amount = float(result.scalar() or 0)
            if status == WithdrawableStatus.LOCKED:
                stats["total_locked"] = amount
            elif status == WithdrawableStatus.COOLDOWN:
                stats["total_cooldown"] = amount
            else:
                stats["total_withdrawable"] = amount
        
        # 按來源統計
        for source in CurrencySource:
            result = await db.execute(
                select(func.sum(LedgerEntry.amount)).where(
                    LedgerEntry.currency_source == source
                )
            )
            amount = float(result.scalar() or 0)
            if amount > 0:
                stats["by_source"].append({
                    "source": source.value,
                    "amount": amount
                })
    except Exception:
        pass
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/liquidity/entries")
async def get_liquidity_entries(
    user_id: Optional[int] = None,
    currency_source: Optional[str] = None,
    withdrawable_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取帳本條目"""
    query = select(LedgerEntry)
    
    conditions = []
    if user_id:
        conditions.append(LedgerEntry.user_id == user_id)
    if currency_source:
        conditions.append(LedgerEntry.currency_source == currency_source)
    if withdrawable_status:
        conditions.append(LedgerEntry.withdrawable_status == withdrawable_status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(LedgerEntry.created_at)).offset((page - 1) * page_size).limit(page_size)
    
    try:
        result = await db.execute(query)
        entries = result.scalars().all()
    except Exception:
        entries = []
    
    # 總數
    count_query = select(func.count(LedgerEntry.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    try:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception:
        total = 0
    
    return {
        "success": True,
        "data": {
            "entries": [
                {
                    "id": entry.id,
                    "user_id": entry.user_id,
                    "category": entry.category.value if entry.category else None,
                    "currency_source": entry.currency_source.value if entry.currency_source else None,
                    "amount": float(entry.amount or 0),
                    "withdrawable_status": entry.withdrawable_status.value if entry.withdrawable_status else None,
                    "unlock_at": entry.unlock_at.isoformat() if entry.unlock_at else None,
                    "turnover_required": float(entry.turnover_required or 0),
                    "turnover_completed": float(entry.turnover_completed or 0),
                    "created_at": entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in entries
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/liquidity/adjust")
async def adjust_liquidity_status(
    request: LiquidityAdjustRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """調整流動性狀態"""
    result = await db.execute(
        select(LedgerEntry).where(
            and_(
                LedgerEntry.id == request.entry_id,
                LedgerEntry.user_id == request.user_id
            )
        )
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="帳本條目不存在")
    
    # 更新狀態
    entry.withdrawable_status = WithdrawableStatus(request.new_status)
    if request.new_status == "withdrawable":
        entry.unlock_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已更新帳本條目狀態為 {request.new_status}"
    }
