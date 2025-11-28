"""
管理后台 - 用户管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from shared.database.connection import get_db_session, get_async_db
from shared.database.models import User, Transaction, RedPacket, RedPacketClaim, CheckinRecord, CurrencyType
from api.utils.auth import get_current_active_admin, AdminUser, get_current_admin
from decimal import Decimal

router = APIRouter(prefix="/api/v1/admin/users", tags=["管理后台-用户管理"])


class UserListItem(BaseModel):
    """用户列表项"""
    id: int
    tg_id: int
    telegram_id: int  # 前端使用的字段名
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    level: int = 1
    balance_usdt: float = 0.0
    balance_ton: float = 0.0
    balance_stars: int = 0
    balance_points: int = 0
    is_banned: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        # 确保 telegram_id 和 tg_id 一致
        if 'telegram_id' not in data and 'tg_id' in data:
            data['telegram_id'] = data['tg_id']
        elif 'tg_id' not in data and 'telegram_id' in data:
            data['tg_id'] = data['telegram_id']
        super().__init__(**data)


@router.get("/list")
async def list_users(
    search: Optional[str] = Query(None, description="搜索关键词（用户名、Telegram ID）"),
    level: Optional[int] = Query(None, description="等级筛选"),
    is_banned: Optional[bool] = Query(None, description="封禁状态筛选"),
    min_balance_usdt: Optional[float] = Query(None, description="最小USDT余额"),
    max_balance_usdt: Optional[float] = Query(None, description="最大USDT余额"),
    created_from: Optional[str] = Query(None, description="注册开始时间（ISO格式）"),
    created_to: Optional[str] = Query(None, description="注册结束时间（ISO格式）"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """获取用户列表（支持搜索和筛选）"""
    query = select(User)
    
    # 搜索条件
    if search:
        try:
            search_int = int(search)
            query = query.where(or_(
                User.tg_id == search_int,
                User.username.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%")
            ))
        except ValueError:
            query = query.where(or_(
                User.username.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%")
            ))
    
    # 筛选条件
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
        except ValueError:
            pass
    
    if created_to:
        try:
            to_date = datetime.fromisoformat(created_to.replace('Z', '+00:00'))
            query = query.where(User.created_at <= to_date)
        except ValueError:
            pass
    
    # 获取总数
    total_count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total_count = total_count_result.scalar_one()
    
    # 分页查询
    offset = (page - 1) * limit
    users_result = await db.execute(
        query.order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    users = users_result.scalars().all()
    
    # 转换为响应模型
    user_list = [
        UserListItem(
            id=user.id,
            tg_id=user.tg_id,
            telegram_id=user.tg_id,  # 添加 telegram_id 字段以兼容前端
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            level=user.level or 1,
            balance_usdt=float(user.balance_usdt or 0),
            balance_ton=float(user.balance_ton or 0),
            balance_stars=user.balance_stars or 0,
            balance_points=user.balance_points or 0,
            is_banned=user.is_banned or False,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]
    
    return {
        "success": True,
        "data": user_list,
        "total": total_count,
        "page": page,
        "limit": limit
    }


class AdjustBalanceRequest(BaseModel):
    user_id: int
    currency: str  # usdt, ton, stars, points
    amount: float
    reason: Optional[str] = None


@router.post("/adjust-balance")
async def adjust_user_balance(
    request: AdjustBalanceRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """调整用户余额"""
    # 获取用户
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 根据货币类型调整余额
    currency_map = {
        "usdt": "balance_usdt",
        "ton": "balance_ton",
        "stars": "balance_stars",
        "points": "balance_points",
    }
    
    if request.currency not in currency_map:
        raise HTTPException(status_code=400, detail=f"不支持的货币类型: {request.currency}")
    
    balance_field = currency_map[request.currency]
    current_balance = getattr(user, balance_field) or Decimal(0)
    if isinstance(current_balance, (int, float)):
        current_balance = Decimal(str(current_balance))
    
    # 更新余额
    amount_decimal = Decimal(str(request.amount))
    new_balance = current_balance + amount_decimal
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="余额不能为负数")
    
    setattr(user, balance_field, new_balance)
    
    # 转换货币类型为枚举
    currency_enum_map = {
        "usdt": CurrencyType.USDT,
        "ton": CurrencyType.TON,
        "stars": CurrencyType.STARS,
        "points": CurrencyType.POINTS,
    }
    currency_enum = currency_enum_map.get(request.currency.lower(), CurrencyType.USDT)
    
    # 创建交易记录
    transaction = Transaction(
        user_id=user.id,
        type="admin_adjust",
        amount=amount_decimal,
        currency=currency_enum,
        balance_before=current_balance,
        balance_after=new_balance,
        note=request.reason or f"管理员 {admin.username} 调整余额",
    )
    db.add(transaction)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "message": "余额调整成功",
        "data": {
            "user_id": user.id,
            "currency": request.currency,
            "old_balance": current_balance,
            "new_balance": new_balance,
            "amount": request.amount,
        }
    }


@router.get("/{user_id}/detail")
async def get_user_detail_full(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """获取用户完整详情（包含交易记录、红包记录、签到记录等）"""
    # 获取用户基本信息
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取交易记录（最近50条）
    transactions_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    transactions = transactions_result.scalars().all()
    
    # 获取发送的红包（最近20个）
    sent_packets_result = await db.execute(
        select(RedPacket)
        .where(RedPacket.sender_id == user.id)
        .order_by(RedPacket.created_at.desc())
        .limit(20)
    )
    sent_packets = sent_packets_result.scalars().all()
    
    # 获取领取的红包记录（最近20条）
    claims_result = await db.execute(
        select(RedPacketClaim)
        .join(RedPacket, RedPacketClaim.red_packet_id == RedPacket.id)
        .where(RedPacketClaim.user_id == user.id)
        .order_by(RedPacketClaim.claimed_at.desc())
        .limit(20)
    )
    claims = claims_result.scalars().all()
    
    # 获取签到记录（最近30天）
    since = datetime.utcnow() - timedelta(days=30)
    checkin_result = await db.execute(
        select(CheckinRecord)
        .where(
            and_(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date >= since
            )
        )
        .order_by(CheckinRecord.checkin_date.desc())
    )
    checkins = checkin_result.scalars().all()
    
    # 统计信息
    # 红包统计
    sent_packets_count_result = await db.execute(
        select(func.count(RedPacket.id)).where(RedPacket.sender_id == user.id)
    )
    sent_packets_count = sent_packets_count_result.scalar() or 0
    
    claimed_packets_count_result = await db.execute(
        select(func.count(RedPacketClaim.id))
        .join(RedPacket, RedPacketClaim.red_packet_id == RedPacket.id)
        .where(RedPacketClaim.user_id == user.id)
    )
    claimed_packets_count = claimed_packets_count_result.scalar() or 0
    
    # 交易统计
    total_transactions_result = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == user.id)
    )
    total_transactions = total_transactions_result.scalar() or 0
    
    return {
        "success": True,
        "data": {
            "user": {
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
                "xp": user.xp or 0,
                "invite_code": user.invite_code,
                "invite_count": user.invite_count or 0,
                "checkin_streak": user.checkin_streak or 0,
                "last_checkin": user.last_checkin.isoformat() if user.last_checkin else None,
                "is_banned": user.is_banned or False,
                "is_admin": user.is_admin or False,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            "statistics": {
                "sent_packets_count": sent_packets_count,
                "claimed_packets_count": claimed_packets_count,
                "total_transactions": total_transactions,
            },
            "transactions": [
                {
                    "id": t.id,
                    "type": t.type,
                    "amount": float(t.amount or 0),
                    "currency": t.currency,
                    "status": t.status,
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in transactions
            ],
            "sent_packets": [
                {
                    "id": p.id,
                    "uuid": p.uuid,
                    "currency": p.currency.value if hasattr(p.currency, 'value') else str(p.currency),
                    "total_amount": float(p.total_amount or 0),
                    "total_count": p.total_count,
                    "claimed_count": p.claimed_count or 0,
                    "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in sent_packets
            ],
            "claimed_packets": [
                {
                    "id": c.id,
                    "red_packet_id": c.red_packet_id,
                    "amount": float(c.amount or 0),
                    "is_luckiest": c.is_luckiest or False,
                    "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
                }
                for c in claims
            ],
            "checkins": [
                {
                    "id": c.id,
                    "checkin_date": c.checkin_date.isoformat() if c.checkin_date else None,
                    "day_of_streak": c.day_of_streak or 0,
                    "reward_points": c.reward_points or 0,
                }
                for c in checkins
            ],
        }
    }


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    user_ids: List[int]
    operation: str  # ban, unban, send_message, export
    data: Optional[dict] = None  # 操作相关数据（如消息内容）


@router.post("/batch-operation")
async def batch_operation(
    request: BatchOperationRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminUser = Depends(get_current_active_admin)
):
    """批量操作（封禁/解封、发送消息、导出）"""
    if not request.user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")
    
    # 获取用户列表
    result = await db.execute(
        select(User).where(User.id.in_(request.user_ids))
    )
    users = result.scalars().all()
    
    if len(users) != len(request.user_ids):
        raise HTTPException(status_code=404, detail="部分用户不存在")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    if request.operation == "ban":
        # 批量封禁
        for user in users:
            try:
                user.is_banned = True
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"用户 {user.id} 封禁失败: {str(e)}")
        
        await db.commit()
        
    elif request.operation == "unban":
        # 批量解封
        for user in users:
            try:
                user.is_banned = False
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"用户 {user.id} 解封失败: {str(e)}")
        
        await db.commit()
        
    elif request.operation == "send_message":
        # 批量发送消息（需要调用 Telegram API）
        message_text = request.data.get("message", "") if request.data else ""
        if not message_text:
            raise HTTPException(status_code=400, detail="消息内容不能为空")
        
        # 调用 Telegram Bot API 发送消息
        try:
            from api.services.telegram_service import TelegramBotService
            telegram_service = TelegramBotService(db=db)
            
            for user in users:
                try:
                    result = await telegram_service.send_message(
                        chat_id=user.tg_id,
                        text=message_text
                    )
                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"用户 {user.tg_id} 发送失败: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    failed_count += 1
                    errors.append(f"用户 {user.tg_id} 发送失败: {str(e)}")
        except ImportError:
            # 如果 Telegram 服务不可用，记录错误
            for user in users:
                failed_count += 1
                errors.append(f"用户 {user.tg_id} 发送失败: Telegram 服务未配置")
        except Exception as e:
            # 其他错误
            for user in users:
                failed_count += 1
                errors.append(f"用户 {user.tg_id} 发送失败: {str(e)}")
        
    elif request.operation == "export":
        # 批量导出（返回用户数据）
        return {
            "success": True,
            "message": "导出数据准备完成",
            "data": {
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
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                    }
                    for user in users
                ]
            }
        }
    else:
        raise HTTPException(status_code=400, detail=f"不支持的操作类型: {request.operation}")
    
    return {
        "success": True,
        "message": f"批量操作完成：成功 {success_count}，失败 {failed_count}",
        "data": {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors if errors else None,
        }
    }

