"""
Lucky Red - 紅包路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import random
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import User, RedPacket, RedPacketClaim, CurrencyType, RedPacketType, RedPacketStatus
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
    
    # 扣除餘額
    setattr(sender, balance_field, current_balance - Decimal(str(request.total_amount)))
    
    # 創建紅包
    packet = RedPacket(
        uuid=str(uuid.uuid4()),
        sender_id=sender.id,
        currency=request.currency,
        packet_type=request.packet_type,
        total_amount=Decimal(str(request.total_amount)),
        total_count=request.total_count,
        message=request.message,
        chat_id=request.chat_id,
        chat_title=request.chat_title,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    
    db.add(packet)
    await db.commit()
    await db.refresh(packet)
    
    # 嘗試發送消息到群組
    message_sent = False
    share_link = None
    
    if request.chat_id:
        try:
            # 構建紅包消息
            currency_symbol = "USDT" if request.currency == CurrencyType.USDT else request.currency.value.upper()
            packet_type_text = "手氣最佳" if request.packet_type == RedPacketType.RANDOM else "紅包炸彈"
            
            text = f"""
🧧 *{sender.first_name or '用戶'} 發了一個紅包*

💰 {float(request.total_amount):.2f} {currency_symbol} | 👥 {request.total_count} 份
🎮 {packet_type_text}
📝 {request.message}

點擊下方按鈕搶紅包！
"""
            
            keyboard = [[InlineKeyboardButton("🧧 搶紅包", callback_data=f"claim:{packet.uuid}")]]
            
            # 嘗試發送消息到群組
            sent_message = await bot.send_message(
                chat_id=request.chat_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # 保存消息 ID
            packet.message_id = sent_message.message_id
            await db.commit()
            message_sent = True
            logger.info(f"Red packet message sent to chat {request.chat_id}, message_id: {sent_message.message_id}")
            
        except TelegramError as e:
            # 如果機器人不在群組中，生成分享鏈接
            error_msg = str(e).lower()
            if "chat not found" in error_msg or "not enough rights" in error_msg or "forbidden" in error_msg:
                logger.warning(f"Bot not in group {request.chat_id} or no permission: {str(e)}")
                # 生成分享鏈接（MiniApp 鏈接，包含紅包 UUID）
                share_link = f"{settings.MINIAPP_URL}/packets/{packet.uuid}"
            else:
                logger.error(f"Failed to send red packet message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending red packet message: {str(e)}")
    
    # 返回響應（包含消息發送狀態）
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
        message_sent=message_sent,
        share_link=share_link
    )
    
    return response


@router.post("/{packet_uuid}/claim", response_model=ClaimResult)
async def claim_red_packet(
    packet_uuid: str,
    claimer_tg_id: int,  # TODO: 從 JWT 獲取
    db: AsyncSession = Depends(get_db_session)
):
    """領取紅包"""
    
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
    
    # 創建領取記錄
    claim = RedPacketClaim(
        red_packet_id=packet.id,
        user_id=claimer.id,
        amount=amount,
    )
    db.add(claim)
    
    # 更新紅包狀態
    packet.claimed_amount += amount
    packet.claimed_count += 1
    
    if packet.claimed_count >= packet.total_count:
        packet.status = RedPacketStatus.COMPLETED
        packet.completed_at = datetime.utcnow()
    
    # 更新用戶餘額
    balance_field = f"balance_{packet.currency.value}"
    current_balance = getattr(claimer, balance_field, 0) or Decimal(0)
    new_balance = current_balance + amount
    setattr(claimer, balance_field, new_balance)
    
    await db.commit()
    
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
        logger.error(f"Failed to send notification: {e}")
    
    return ClaimResult(
        success=True,
        amount=float(amount),
        is_luckiest=False,  # TODO: 計算手氣最佳
        message=f"恭喜獲得 {amount} {packet.currency.value.upper()}！"
    )


@router.get("/list", response_model=List[RedPacketResponse])
async def list_red_packets(
    status: Optional[RedPacketStatus] = None,
    chat_id: Optional[int] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取紅包列表"""
    query = select(RedPacket).order_by(RedPacket.created_at.desc()).limit(limit)
    
    if status:
        query = query.where(RedPacket.status == status)
    if chat_id:
        query = query.where(RedPacket.chat_id == chat_id)
    
    result = await db.execute(query)
    packets = result.scalars().all()
    
    return packets

