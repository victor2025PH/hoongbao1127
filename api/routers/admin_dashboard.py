"""
管理后台 - 仪表盘路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional

from shared.database.connection import get_db_session
from shared.database.models import User, RedPacket, Transaction, RedPacketClaim, CheckinRecord
from api.utils.auth import get_current_active_admin, AdminUser

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["管理后台-仪表盘"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取儀表盤統計數據"""
    # 用戶統計
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    today = datetime.utcnow().date()
    new_users_today_result = await db.execute(
        select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
    )
    new_users_today = new_users_today_result.scalar() or 0
    
    # 紅包統計
    total_packets_result = await db.execute(select(func.count(RedPacket.id)))
    total_packets = total_packets_result.scalar() or 0
    
    active_packets_result = await db.execute(
        select(func.count(RedPacket.id)).where(
            RedPacket.status == "active"
        )
    )
    active_packets = active_packets_result.scalar() or 0
    
    # 交易統計
    total_transactions_result = await db.execute(select(func.count(Transaction.id)))
    total_transactions = total_transactions_result.scalar() or 0
    
    total_volume_result = await db.execute(select(func.sum(Transaction.amount)))
    total_volume = float(total_volume_result.scalar() or 0)
    
    # 簽到統計
    total_checkins_result = await db.execute(select(func.count(CheckinRecord.id)))
    total_checkins = total_checkins_result.scalar() or 0
    
    today_checkins_result = await db.execute(
        select(func.count(CheckinRecord.id)).where(
            func.date(CheckinRecord.checkin_date) == today
        )
    )
    today_checkins = today_checkins_result.scalar() or 0
    
    # 邀請統計
    total_invites_result = await db.execute(
        select(func.sum(User.invite_count))
    )
    total_invites = int(total_invites_result.scalar() or 0)
    
    active_inviters_result = await db.execute(
        select(func.count(User.id)).where(User.invite_count > 0)
    )
    active_inviters = active_inviters_result.scalar() or 0
    
    return {
        "success": True,
        "data": {
            "users": {
                "total": total_users,
                "new_today": new_users_today
            },
            "red_packets": {
                "total": total_packets,
                "active": active_packets
            },
            "transactions": {
                "total": total_transactions,
                "volume": total_volume
            },
            "checkin": {
                "total": total_checkins,
                "today": today_checkins
            },
            "invite": {
                "total": total_invites,
                "active_inviters": active_inviters
            }
        }
    }


@router.get("/trends")
async def get_dashboard_trends(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取儀表盤趨勢數據（用於圖表）"""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # 生成日期列表
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    # 用戶增長趨勢
    user_trends = []
    for date in date_list:
        count_result = await db.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == date
            )
        )
        count = count_result.scalar() or 0
        user_trends.append({
            "date": date.isoformat(),
            "count": count
        })
    
    # 紅包創建趨勢
    packet_trends = []
    for date in date_list:
        count_result = await db.execute(
            select(func.count(RedPacket.id)).where(
                func.date(RedPacket.created_at) == date
            )
        )
        count = count_result.scalar() or 0
        packet_trends.append({
            "date": date.isoformat(),
            "count": count
        })
    
    # 交易趨勢（按日期和貨幣類型）
    transaction_trends = []
    for date in date_list:
        # 獲取當日所有交易
        transactions_result = await db.execute(
            select(Transaction).where(
                func.date(Transaction.created_at) == date
            )
        )
        transactions = transactions_result.scalars().all()
        
        # 按貨幣類型統計
        by_currency = {}
        total_amount = 0
        for txn in transactions:
            currency = txn.currency.value if hasattr(txn.currency, 'value') else str(txn.currency)
            amount = float(txn.amount or 0)
            by_currency[currency] = by_currency.get(currency, 0) + amount
            total_amount += amount
        
        transaction_trends.append({
            "date": date.isoformat(),
            "total_amount": total_amount,
            "count": len(transactions),
            "by_currency": by_currency
        })
    
    # 紅包領取趨勢
    claim_trends = []
    for date in date_list:
        count_result = await db.execute(
            select(func.count(RedPacketClaim.id)).where(
                func.date(RedPacketClaim.claimed_at) == date
            )
        )
        count = count_result.scalar() or 0
        
        amount_result = await db.execute(
            select(func.sum(RedPacketClaim.amount)).where(
                func.date(RedPacketClaim.claimed_at) == date
            )
        )
        amount = float(amount_result.scalar() or 0)
        
        claim_trends.append({
            "date": date.isoformat(),
            "count": count,
            "amount": amount
        })
    
    return {
        "success": True,
        "data": {
            "user_trends": user_trends,
            "packet_trends": packet_trends,
            "transaction_trends": transaction_trends,
            "claim_trends": claim_trends,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
    }


@router.get("/distribution")
async def get_dashboard_distribution(
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """獲取數據分布（用於餅圖等）"""
    # 用戶等級分布
    level_distribution = []
    for level in range(1, 11):  # 假設等級 1-10
        count_result = await db.execute(
            select(func.count(User.id)).where(User.level == level)
        )
        count = count_result.scalar() or 0
        if count > 0:
            level_distribution.append({
                "level": level,
                "count": count
            })
    
    # 紅包狀態分布
    status_distribution = []
    statuses = ["active", "completed", "expired", "refunded"]
    for status in statuses:
        count_result = await db.execute(
            select(func.count(RedPacket.id)).where(RedPacket.status == status)
        )
        count = count_result.scalar() or 0
        if count > 0:
            status_distribution.append({
                "status": status,
                "count": count
            })
    
    # 交易類型分布
    type_distribution = []
    transaction_types = await db.execute(
        select(Transaction.type, func.count(Transaction.id).label("count"))
        .group_by(Transaction.type)
    )
    for row in transaction_types:
        type_distribution.append({
            "type": row.type,
            "count": row.count
        })
    
    # 貨幣餘額分布（按餘額區間）
    balance_ranges = [
        {"min": 0, "max": 10, "label": "0-10"},
        {"min": 10, "max": 100, "label": "10-100"},
        {"min": 100, "max": 1000, "label": "100-1000"},
        {"min": 1000, "max": float('inf'), "label": "1000+"}
    ]
    
    balance_distribution = []
    for range_item in balance_ranges:
        if range_item["max"] == float('inf'):
            count_result = await db.execute(
                select(func.count(User.id)).where(User.balance_usdt >= range_item["min"])
            )
        else:
            count_result = await db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.balance_usdt >= range_item["min"],
                        User.balance_usdt < range_item["max"]
                    )
                )
            )
        count = count_result.scalar() or 0
        if count > 0:
            balance_distribution.append({
                "range": range_item["label"],
                "count": count
            })
    
    return {
        "success": True,
        "data": {
            "level_distribution": level_distribution,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "balance_distribution": balance_distribution
        }
    }

