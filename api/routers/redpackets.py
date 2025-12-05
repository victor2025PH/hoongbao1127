"""
Lucky Red - 紅包路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import random
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import (
    User, RedPacket, RedPacketClaim, CurrencyType, RedPacketType, RedPacketStatus,
    RedPacketVisibility, RedPacketSource
)
from shared.config.settings import get_settings
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from api.utils.telegram_auth import get_tg_id_from_header

settings = get_settings()
router = APIRouter()
bot = Bot(token=settings.BOT_TOKEN)


class CreateRedPacketRequest(BaseModel):
    """創建紅包請求"""
    currency: Union[CurrencyType, str] = CurrencyType.USDT
    packet_type: Union[RedPacketType, str] = RedPacketType.RANDOM
    total_amount: float = Field(..., gt=0)
    total_count: int = Field(..., ge=1, le=100)
    message: str = Field(default="恭喜發財！🧧", max_length=256)
    chat_id: Optional[int] = None
    chat_title: Optional[str] = None
    bomb_number: Optional[int] = None  # 紅包炸彈數字（0-9）
    
    @field_validator('currency', mode='before')
    @classmethod
    def normalize_currency(cls, v):
        """將 currency 轉換為小寫並映射到 CurrencyType 枚舉"""
        if isinstance(v, str):
            v_lower = v.lower()
            currency_map = {
                "usdt": CurrencyType.USDT,
                "ton": CurrencyType.TON,
                "stars": CurrencyType.STARS,
                "points": CurrencyType.POINTS,
            }
            return currency_map.get(v_lower, CurrencyType.USDT)
        return v
    
    @field_validator('packet_type', mode='before')
    @classmethod
    def normalize_packet_type(cls, v):
        """將 packet_type 轉換並映射到 RedPacketType 枚舉"""
        if isinstance(v, str):
            v_lower = v.lower()
            # 映射前端使用的 'fixed' 到后端的 'equal'（平分）
            packet_type_map = {
                "random": RedPacketType.RANDOM,
                "fixed": RedPacketType.EQUAL,  # 固定金額 = 平分
                "equal": RedPacketType.EQUAL,
                "exclusive": RedPacketType.EXCLUSIVE,
            }
            return packet_type_map.get(v_lower, RedPacketType.RANDOM)
        return v


class RedPacketResponse(BaseModel):
    """紅包響應"""
    id: int
    uuid: str
    currency: str
    packet_type: str
    total_amount: float
    total_count: int
    claimed_amount: float
    claimed_count: int
    message: str
    status: str
    created_at: datetime
    message_sent: bool = False  # 消息是否成功發送到群組
    share_link: Optional[str] = None  # 分享鏈接（如果機器人不在群組中）
    
    class Config:
        from_attributes = True


class ClaimResult(BaseModel):
    """領取結果"""
    success: bool
    amount: float
    is_luckiest: bool
    message: str


@router.post("/create", response_model=RedPacketResponse)
async def create_red_packet(
    request: CreateRedPacketRequest,
    sender_tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """創建紅包"""
    if sender_tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 查找發送者
    result = await db.execute(select(User).where(User.tg_id == sender_tg_id))
    sender = result.scalar_one_or_none()
    
    if not sender:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 檢查餘額
    balance_field = f"balance_{request.currency.value}"
    current_balance = getattr(sender, balance_field, 0) or Decimal(0)
    
    if current_balance < Decimal(str(request.total_amount)):
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # 驗證紅包炸彈規則
    if request.packet_type == RedPacketType.EQUAL:  # 紅包炸彈（固定金額）
        if request.bomb_number is None:
            raise HTTPException(status_code=400, detail="Bomb number is required for bomb red packet")
        if request.bomb_number < 0 or request.bomb_number > 9:
            raise HTTPException(status_code=400, detail="Bomb number must be between 0 and 9")
        
        # 驗證紅包數量：單雷10個，雙雷5個
        if request.total_count not in [5, 10]:
            raise HTTPException(
                status_code=400,
                detail="Bomb red packet count must be 5 (雙雷) or 10 (單雷)"
            )
    
    # 扣除餘額
    setattr(sender, balance_field, current_balance - Decimal(str(request.total_amount)))
    
    # 判斷紅包可見性和來源類型
    if request.chat_id is None:
        # 公開紅包
        visibility = RedPacketVisibility.PUBLIC
        source_type = RedPacketSource.USER_PUBLIC
    else:
        # 私密紅包
        visibility = RedPacketVisibility.PRIVATE
        source_type = RedPacketSource.USER_PRIVATE
    
    # 創建紅包
    packet = RedPacket(
        uuid=str(uuid.uuid4()),
        sender_id=sender.id,
        currency=request.currency,
        packet_type=request.packet_type,
        total_amount=Decimal(str(request.total_amount)),
        total_count=request.total_count,
        message=request.message,
        chat_id=request.chat_id,  # 公開紅包時為 NULL
        chat_title=request.chat_title,
        bomb_number=request.bomb_number if request.packet_type == RedPacketType.EQUAL else None,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        visibility=visibility,
        source_type=source_type,
    )
    
    db.add(packet)
    await db.commit()
    await db.refresh(packet)
    
    # 融合任務系統：標記發紅包任務完成
    try:
        from api.routers.tasks import mark_task_complete_internal
        # 異步調用任務完成標記（不阻塞創建響應）
        import asyncio
        asyncio.create_task(mark_task_complete_internal("send_packet", sender_tg_id, db))
    except Exception as e:
        logger.warning(f"Failed to mark send_packet task complete: {e}")
    
    # ⚠️ 注意：不再在 API 路由中發送紅包消息
    # 改由 Bot 處理器統一發送，避免重複發送
    # 如果機器人不在群組中，返回 share_link 供前端使用
    
    # 檢查機器人是否在群組中（僅用於返回 share_link）
    message_sent = False
    share_link = None
    if request.chat_id:
        try:
            bot_info = await bot.get_me()
            bot_member = await bot.get_chat_member(request.chat_id, bot_info.id)
            bot_status = bot_member.status
            if bot_status not in ['left', 'kicked']:
                # 機器人在群組中，Bot 處理器會發送消息
                message_sent = True
            else:
                # 機器人不在群組中，返回分享鏈接
                share_link = f"{settings.MINIAPP_URL}/claim/{packet.uuid}"
        except TelegramError as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg or "not enough rights" in error_msg or "forbidden" in error_msg:
                # 機器人不在群組中，返回分享鏈接
                share_link = f"{settings.MINIAPP_URL}/claim/{packet.uuid}"
        except Exception as e:
            logger.warning(f"Error checking bot membership: {e}")
            # 無法確定，假設機器人在群組中
    
    # 返回響應
    response = RedPacketResponse(
        id=packet.id,
        uuid=packet.uuid,
        currency=packet.currency.value,
        packet_type=packet.packet_type.value,
        total_amount=float(packet.total_amount),
        total_count=packet.total_count,
        claimed_amount=float(packet.claimed_amount),
        claimed_count=packet.claimed_count,
        message=packet.message,
        status=packet.status.value,
        created_at=packet.created_at,
        message_sent=message_sent,  # 機器人在群組中時為 True
        share_link=share_link  # 機器人不在群組中時返回分享鏈接
    )
    
    return response


@router.post("/{packet_uuid}/claim", response_model=ClaimResult)
async def claim_red_packet(
    packet_uuid: str,
    claimer_tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """領取紅包"""
    
    if claimer_tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 查找紅包
    result = await db.execute(select(RedPacket).where(RedPacket.uuid == packet_uuid))
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Red packet not found")
    
    if packet.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Red packet is not active")
    
    if packet.expires_at and packet.expires_at < datetime.utcnow():
        packet.status = RedPacketStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Red packet expired")
    
    # 查找領取者
    result = await db.execute(select(User).where(User.tg_id == claimer_tg_id))
    claimer = result.scalar_one_or_none()
    
    if not claimer:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 檢查是否已領取
    result = await db.execute(
        select(RedPacketClaim).where(
            and_(
                RedPacketClaim.red_packet_id == packet.id,
                RedPacketClaim.user_id == claimer.id
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already claimed")
    
    # 計算領取金額
    remaining_amount = packet.total_amount - packet.claimed_amount
    remaining_count = packet.total_count - packet.claimed_count
    
    if remaining_count <= 0:
        packet.status = RedPacketStatus.COMPLETED
        await db.commit()
        raise HTTPException(status_code=400, detail="Red packet is empty")
    
    if packet.packet_type == RedPacketType.EQUAL:
        amount = remaining_amount / remaining_count
    else:
        # 隨機金額 (保證最後一個人能拿到剩餘)
        if remaining_count == 1:
            amount = remaining_amount
        else:
            max_amount = remaining_amount * Decimal("0.9") / remaining_count * 2
            amount = Decimal(str(random.uniform(0.01, float(max_amount))))
            amount = min(amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
    
    amount = round(amount, 8)
    
    # 紅包炸彈：檢查是否踩雷
    is_bomb = False
    penalty_amount = Decimal(0)
    
    if packet.packet_type == RedPacketType.EQUAL and packet.bomb_number is not None:
        # 獲取金額的最後一位有效數字
        # 方法：將金額轉換為整數（乘以100000000，保留8位小數精度），然後取模10
        # 這樣可以準確獲取最後一位數字，不受小數點影響
        amount_int = int(amount * Decimal("100000000"))  # 轉換為整數（8位小數精度）
        last_digit = amount_int % 10  # 取最後一位數字
        
        # 檢查是否等於炸彈數字
        if last_digit == packet.bomb_number:
            is_bomb = True
            # 計算賠付：單雷（10個）賠1倍，雙雷（5個）賠2倍
            multiplier = 1 if packet.total_count == 10 else 2
            penalty_amount = amount * Decimal(multiplier)
    
    # 創建領取記錄
    claim = RedPacketClaim(
        red_packet_id=packet.id,
        user_id=claimer.id,
        amount=amount,
        is_bomb=is_bomb,
        penalty_amount=penalty_amount if is_bomb else None,
    )
    db.add(claim)
    
    # 更新紅包狀態
    packet.claimed_amount += amount
    packet.claimed_count += 1
    
    is_luckiest = False
    is_completed = packet.claimed_count >= packet.total_count
    
    if is_completed:
        packet.status = RedPacketStatus.COMPLETED
        packet.completed_at = datetime.utcnow()
    
    # 更新用戶餘額
    balance_field = f"balance_{packet.currency.value}"
    current_balance = getattr(claimer, balance_field, 0) or Decimal(0)
    # 先加上領取金額
    new_balance = current_balance + amount
    # 如果踩雷，扣除賠付金額
    if is_bomb:
        new_balance = new_balance - penalty_amount
        # 檢查餘額是否足夠賠付
        if new_balance < 0:
            # 如果餘額不足，只扣除現有餘額（不能為負）
            actual_penalty = current_balance + amount
            new_balance = Decimal(0)
            penalty_amount = actual_penalty
            claim.penalty_amount = penalty_amount
        # 將賠付金額轉給發送者
        sender_result = await db.execute(select(User).where(User.id == packet.sender_id))
        sender = sender_result.scalar_one_or_none()
        if sender:
            sender_balance = getattr(sender, balance_field, 0) or Decimal(0)
            setattr(sender, balance_field, sender_balance + penalty_amount)
    
    setattr(claimer, balance_field, new_balance)
    
    # 先提交以便查詢包含當前的 claim
    await db.commit()
    await db.refresh(claim)
    
    # 計算手氣最佳（僅對隨機紅包，且紅包已領完）
    if is_completed and packet.packet_type == RedPacketType.RANDOM:
        # 查詢所有領取記錄，按金額降序、領取時間升序排序
        # 這樣可以找出金額最大的，如果金額相同則選最早領取的
        result = await db.execute(
            select(RedPacketClaim)
            .where(RedPacketClaim.red_packet_id == packet.id)
            .order_by(desc(RedPacketClaim.amount), asc(RedPacketClaim.claimed_at))
        )
        all_claims = result.scalars().all()
        
        if all_claims:
            # 第一個就是手氣最佳的（金額最大，如果相同則最早領取）
            luckiest_claim = all_claims[0]
            luckiest_claim.is_luckiest = True
            # 如果當前領取者是最佳手氣
            if luckiest_claim.id == claim.id:
                is_luckiest = True
            await db.commit()
    
    # 紅包領完後發送群組通知
    if is_completed and packet.chat_id:
        try:
            from api.services.group_notification_service import notify_packet_result
            await notify_packet_result(db, packet.id)
        except Exception as e:
            logger.error(f"Failed to send group notification: {e}")
    
    # 發送消息通知（異步，不阻塞響應）
    try:
        from api.services.message_service import MessageService
        message_service = MessageService(db)
        await message_service.send_redpacket_notification(
            user_id=claimer.id,
            redpacket_id=packet.id,
            amount=float(amount),
            currency=packet.currency.value,
            is_claimed=True
        )
        # 發送餘額變動通知
        await message_service.send_balance_notification(
            user_id=claimer.id,
            amount=float(amount),
            currency=packet.currency.value,
            transaction_type="receive",
            balance_after=float(new_balance)
        )
    except Exception as e:
        logger.error(f"Failed to send message notification: {e}")
    
    # WebSocket 實時推送
    try:
        from api.services.notification_service import notification_service
        # 通知領取者（餘額變動）
        await notification_service.notify_packet_claimed(
            db, claimer.id, packet.sender_id, 
            amount - penalty_amount if is_bomb else amount,
            packet.currency.value, str(packet.id),
            is_bomb=is_bomb, is_lucky=is_luckiest
        )
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")
    
    # 構建消息
    if is_bomb:
        message = f"💣 踩雷了！獲得 {amount} {packet.currency.value.upper()}，但需賠付 {penalty_amount} {packet.currency.value.upper()}！"
    else:
        message = f"恭喜獲得 {amount} {packet.currency.value.upper()}！"
        if is_luckiest:
            message += " 🎉 手氣最佳！"
    
    return ClaimResult(
        success=True,
        amount=float(amount - penalty_amount if is_bomb else amount),  # 實際到賬金額
        is_luckiest=is_luckiest,
        message=message
    )


@router.get("/list", response_model=List[RedPacketResponse])
@router.get("", response_model=List[RedPacketResponse])  # 兼容 /api/redpackets 路径
async def list_red_packets(
    status: Optional[RedPacketStatus] = None,
    chat_id: Optional[int] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    """
    獲取公開紅包列表
    
    只返回公開紅包（chat_id 為 NULL），不包含發送到指定群組或用戶的私密紅包。
    公開紅包包括：
    - 用戶主動發送的公開隨機紅包
    - 任務紅包（需要完成任務才能領取）
    - 獎勵紅包（系統獎勵、活動獎勵等）
    """
    # 默认只返回活跃红包
    if status is None:
        status = RedPacketStatus.ACTIVE
    
    query = select(RedPacket).order_by(RedPacket.created_at.desc()).limit(limit)
    
    # 只返回公開紅包（chat_id 為 NULL）
    # 私密紅包（發送到指定群組或用戶的）不顯示在公開頁面
    query = query.where(RedPacket.chat_id.is_(None))
    
    # 过滤状态
    query = query.where(RedPacket.status == status)
    
    # 过滤过期红包
    query = query.where(RedPacket.expires_at > datetime.utcnow())
    
    # 如果指定了 chat_id，則只返回該群組的公開紅包（通常不會用到）
    if chat_id:
        query = query.where(RedPacket.chat_id == chat_id)
    
    result = await db.execute(query)
    packets = result.scalars().all()
    
    return packets


@router.get("/recommended", response_model=List[RedPacketResponse])
async def get_recommended_packets(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取推薦紅包（根據用戶活躍度）"""
    from sqlalchemy import case, func as sql_func
    
    # 計算用戶活躍度
    activity_score = 0
    if tg_id:
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            # 活躍度計算：簽到天數 + 邀請人數 + 搶包次數 + 發包次數
            checkin_days = (user.total_checkin_count or 0) * 10
            invite_count = (user.invite_count or 0) * 5
            claim_count_result = await db.execute(
                select(sql_func.count(RedPacketClaim.id)).where(RedPacketClaim.user_id == user.id)
            )
            claim_count = claim_count_result.scalar() or 0
            send_count_result = await db.execute(
                select(sql_func.count(RedPacket.id)).where(RedPacket.sender_id == user.id)
            )
            send_count = send_count_result.scalar() or 0
            activity_score = checkin_days + invite_count + claim_count + send_count
    
    # 獲取推薦紅包（只返回公開紅包和任務紅包）
    query = select(RedPacket).where(
        RedPacket.status == RedPacketStatus.ACTIVE,
        RedPacket.expires_at > datetime.utcnow(),
        RedPacket.chat_id.is_(None)  # 只返回公開紅包
    )
    
    # 根據活躍度排序
    if activity_score > 50:
        # 活躍用戶：優先推薦高價值紅包和任務紅包
        query = query.order_by(
            case(
                (RedPacket.source_type == RedPacketSource.TASK, 0),
                (RedPacket.source_type == RedPacketSource.REWARD, 1),
                else_=2
            ),
            RedPacket.total_amount.desc(),
            RedPacket.created_at.desc()
        )
    else:
        # 新用戶：優先推薦任務紅包和公開紅包
        query = query.order_by(
            case(
                (RedPacket.source_type == RedPacketSource.TASK, 0),
                (RedPacket.visibility == RedPacketVisibility.PUBLIC, 1),
                else_=2
            ),
            RedPacket.created_at.desc()
        )
    
    result = await db.execute(query.limit(limit))
    packets = result.scalars().all()
    
    # 轉換為響應格式
    responses = []
    for packet in packets:
        responses.append(RedPacketResponse(
            id=packet.id,
            uuid=packet.uuid,
            currency=packet.currency.value,
            packet_type=packet.packet_type.value,
            total_amount=float(packet.total_amount),
            total_count=packet.total_count,
            claimed_amount=float(packet.claimed_amount),
            claimed_count=packet.claimed_count,
            message=packet.message,
            status=packet.status.value,
            created_at=packet.created_at,
            message_sent=False,
            share_link=None
        ))
    
    return responses

