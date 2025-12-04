"""
Lucky Red - AI 系統對接 API
允許外部 AI 聊天系統調用紅包遊戲功能

文件路徑：c:\hbgm001\api\routers\ai_api.py
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import hashlib
import random
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import (
    User, RedPacket, RedPacketClaim, Transaction,
    CurrencyType, RedPacketType, RedPacketStatus
)
from shared.config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v2/ai", tags=["AI 系統對接"])


# ============================================================
# 請求/響應模型
# ============================================================

class AIPacketSendRequest(BaseModel):
    """AI 發送紅包請求"""
    currency: str = Field(default="usdt", description="幣種: usdt, ton, stars, points")
    packet_type: str = Field(default="random", description="類型: random(手氣), equal(炸彈)")
    total_amount: float = Field(..., gt=0, description="總金額")
    total_count: int = Field(..., ge=1, le=100, description="份數")
    message: str = Field(default="🤖 AI 紅包", max_length=256, description="祝福語")
    chat_id: Optional[int] = Field(None, description="目標群組 ID（可選）")
    bomb_number: Optional[int] = Field(None, ge=0, le=9, description="炸彈數字 0-9（炸彈紅包必填）")


class AIPacketClaimRequest(BaseModel):
    """AI 領取紅包請求"""
    packet_uuid: str = Field(..., description="紅包 UUID")


class AITransferRequest(BaseModel):
    """AI 轉帳請求"""
    to_user_id: int = Field(..., description="接收者 Telegram ID")
    currency: str = Field(default="usdt", description="幣種")
    amount: float = Field(..., gt=0, description="金額")
    note: Optional[str] = Field(None, max_length=256, description="備註")


class AIResponse(BaseModel):
    """AI API 統一響應"""
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat()})


# ============================================================
# AI 系統認證
# ============================================================

# 簡化版：使用環境變數或配置的 API Key
# 生產環境應使用資料庫表管理
AI_API_KEYS = {
    # "api_key_hash": {"system_name": "xxx", "permissions": [...]}
}


async def verify_ai_api_key(
    authorization: str = Header(..., description="Bearer <API_KEY>"),
    x_telegram_user_id: int = Header(..., alias="X-Telegram-User-Id"),
    x_ai_system_id: str = Header(None, alias="X-AI-System-Id"),
    db: AsyncSession = Depends(get_db_session)
) -> tuple[int, dict]:
    """
    驗證 AI 系統 API Key 並獲取代表的用戶
    
    返回: (telegram_user_id, api_key_info)
    """
    # 解析 Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    api_key = authorization[7:]
    
    # 驗證 API Key
    # TODO: 從資料庫查詢並驗證
    # 簡化版：使用配置的金鑰
    expected_key = settings.AI_API_KEY if hasattr(settings, 'AI_API_KEY') else None
    
    if not expected_key:
        # 開發模式：允許任意 key
        logger.warning("AI API Key not configured, allowing any key in dev mode")
        if not settings.DEBUG:
            raise HTTPException(status_code=401, detail="AI API not configured")
    elif api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 驗證用戶存在
    result = await db.execute(select(User).where(User.tg_id == x_telegram_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail=f"User with Telegram ID {x_telegram_user_id} not found"
        )
    
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")
    
    api_key_info = {
        "system_id": x_ai_system_id or "unknown",
        "user_db_id": user.id,
    }
    
    logger.info(f"AI API call: system={x_ai_system_id}, user={x_telegram_user_id}")
    
    return x_telegram_user_id, api_key_info


# ============================================================
# API 端點
# ============================================================

@router.get("/status")
async def ai_api_status():
    """AI API 健康檢查"""
    return AIResponse(
        success=True,
        data={
            "status": "ok",
            "version": "2.0",
            "endpoints": [
                "GET /api/v2/ai/status",
                "GET /api/v2/ai/wallet/balance",
                "GET /api/v2/ai/user/profile",
                "POST /api/v2/ai/packets/send",
                "POST /api/v2/ai/packets/claim",
                "POST /api/v2/ai/wallet/transfer",
            ]
        }
    )


@router.get("/wallet/balance")
async def ai_get_balance(
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 獲取用戶餘額
    
    Headers:
    - Authorization: Bearer <API_KEY>
    - X-Telegram-User-Id: 123456789
    """
    tg_id, key_info = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usdt = float(user.balance_usdt or 0)
    ton = float(user.balance_ton or 0)
    stars = user.balance_stars or 0
    points = user.balance_points or 0
    
    # 簡單折算成 USDT
    total_usdt = usdt + ton * 5.0 + stars * 0.01 + points * 0.001
    
    return AIResponse(
        success=True,
        data={
            "user_id": tg_id,
            "balances": {
                "usdt": usdt,
                "ton": ton,
                "stars": stars,
                "points": points
            },
            "total_usdt_equivalent": round(total_usdt, 2)
        }
    )


@router.get("/user/profile")
async def ai_get_user_profile(
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 獲取用戶資料
    
    Headers:
    - Authorization: Bearer <API_KEY>
    - X-Telegram-User-Id: 123456789
    """
    tg_id, key_info = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 統計紅包數據
    sent_result = await db.execute(
        select(RedPacket).where(RedPacket.sender_id == user.id)
    )
    sent_packets = sent_result.scalars().all()
    
    claim_result = await db.execute(
        select(RedPacketClaim).where(RedPacketClaim.user_id == user.id)
    )
    claims = claim_result.scalars().all()
    
    return AIResponse(
        success=True,
        data={
            "user_id": tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "level": user.level or 1,
            "xp": user.xp or 0,
            "invite_code": user.invite_code,
            "invite_count": user.invite_count or 0,
            "packets_sent": len(sent_packets),
            "packets_claimed": len(claims),
            "total_sent_amount": float(sum(p.total_amount for p in sent_packets)),
            "total_claimed_amount": float(sum(c.amount for c in claims)),
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )


@router.post("/packets/send")
async def ai_send_packet(
    request: AIPacketSendRequest,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 代替用戶發送紅包
    
    Headers:
    - Authorization: Bearer <API_KEY>
    - X-Telegram-User-Id: 123456789
    
    Body:
    {
        "currency": "usdt",
        "packet_type": "random",
        "total_amount": 10.0,
        "total_count": 5,
        "message": "AI 紅包"
    }
    """
    tg_id, key_info = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 映射幣種
    currency_map = {
        "usdt": CurrencyType.USDT,
        "ton": CurrencyType.TON,
        "stars": CurrencyType.STARS,
        "points": CurrencyType.POINTS,
    }
    currency = currency_map.get(request.currency.lower())
    if not currency:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {request.currency}")
    
    # 映射紅包類型
    packet_type_map = {
        "random": RedPacketType.RANDOM,
        "equal": RedPacketType.EQUAL,
    }
    packet_type = packet_type_map.get(request.packet_type.lower())
    if not packet_type:
        raise HTTPException(status_code=400, detail=f"Invalid packet_type: {request.packet_type}")
    
    # 檢查炸彈紅包
    if packet_type == RedPacketType.EQUAL:
        if request.bomb_number is None:
            raise HTTPException(status_code=400, detail="bomb_number required for bomb packet")
        if request.total_count not in [5, 10]:
            raise HTTPException(status_code=400, detail="Bomb packet count must be 5 or 10")
    
    # 檢查餘額
    balance_field = f"balance_{currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    amount = Decimal(str(request.total_amount))
    
    if current_balance < amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance: {current_balance} < {amount} {currency.value.upper()}"
        )
    
    # 扣除餘額
    setattr(user, balance_field, current_balance - amount)
    
    # 創建紅包
    packet = RedPacket(
        uuid=str(uuid.uuid4()),
        sender_id=user.id,
        currency=currency,
        packet_type=packet_type,
        total_amount=amount,
        total_count=request.total_count,
        message=request.message,
        chat_id=request.chat_id,
        bomb_number=request.bomb_number if packet_type == RedPacketType.EQUAL else None,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    
    db.add(packet)
    await db.commit()
    await db.refresh(packet)
    
    logger.info(f"AI created packet: uuid={packet.uuid}, sender={tg_id}, amount={amount}")
    
    # 生成分享連結
    share_url = f"https://t.me/{settings.BOT_USERNAME}/app?startapp=p_{packet.uuid}"
    deep_link = f"{settings.MINIAPP_URL}/packets/{packet.uuid}"
    
    return AIResponse(
        success=True,
        data={
            "packet_id": packet.uuid,
            "packet_type": packet.packet_type.value,
            "total_amount": float(packet.total_amount),
            "total_count": packet.total_count,
            "currency": packet.currency.value,
            "share_url": share_url,
            "deep_link": deep_link,
            "remaining_balance": float(current_balance - amount),
            "expires_at": packet.expires_at.isoformat()
        }
    )


@router.post("/packets/claim")
async def ai_claim_packet(
    request: AIPacketClaimRequest,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 代替用戶領取紅包
    
    Headers:
    - Authorization: Bearer <API_KEY>
    - X-Telegram-User-Id: 987654321
    
    Body:
    {
        "packet_uuid": "xxx-xxx-xxx"
    }
    """
    tg_id, key_info = auth
    
    # 查找用戶
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    claimer = result.scalar_one_or_none()
    
    if not claimer:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 查找紅包
    result = await db.execute(select(RedPacket).where(RedPacket.uuid == request.packet_uuid))
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")
    
    if packet.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Packet is not active")
    
    if packet.expires_at and packet.expires_at < datetime.utcnow():
        packet.status = RedPacketStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Packet expired")
    
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
        raise HTTPException(status_code=400, detail="Packet is empty")
    
    if packet.packet_type == RedPacketType.EQUAL:
        amount = remaining_amount / remaining_count
    else:
        if remaining_count == 1:
            amount = remaining_amount
        else:
            max_amount = remaining_amount * Decimal("0.9") / remaining_count * 2
            amount = Decimal(str(random.uniform(0.01, float(max_amount))))
            amount = min(amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
    
    amount = round(amount, 8)
    
    # 檢查踩雷
    is_bomb = False
    penalty_amount = Decimal(0)
    
    if packet.packet_type == RedPacketType.EQUAL and packet.bomb_number is not None:
        amount_int = int(amount * Decimal("100000000"))
        last_digit = amount_int % 10
        
        if last_digit == packet.bomb_number:
            is_bomb = True
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
    
    is_completed = packet.claimed_count >= packet.total_count
    if is_completed:
        packet.status = RedPacketStatus.COMPLETED
        packet.completed_at = datetime.utcnow()
    
    # 更新用戶餘額
    balance_field = f"balance_{packet.currency.value}"
    current_balance = getattr(claimer, balance_field, 0) or Decimal(0)
    new_balance = current_balance + amount
    
    if is_bomb:
        new_balance = new_balance - penalty_amount
        if new_balance < 0:
            penalty_amount = current_balance + amount
            new_balance = Decimal(0)
            claim.penalty_amount = penalty_amount
        
        # 賠付給發送者
        sender_result = await db.execute(select(User).where(User.id == packet.sender_id))
        sender = sender_result.scalar_one_or_none()
        if sender:
            sender_balance = getattr(sender, balance_field, 0) or Decimal(0)
            setattr(sender, balance_field, sender_balance + penalty_amount)
    
    setattr(claimer, balance_field, new_balance)
    
    await db.commit()
    
    logger.info(f"AI claimed packet: uuid={request.packet_uuid}, claimer={tg_id}, amount={amount}")
    
    actual_amount = amount - penalty_amount if is_bomb else amount
    
    return AIResponse(
        success=True,
        data={
            "packet_uuid": packet.uuid,
            "claimed_amount": float(amount),
            "actual_amount": float(actual_amount),
            "is_luckiest": False,  # 需要紅包完成後才能判斷
            "is_bomb": is_bomb,
            "penalty_amount": float(penalty_amount) if is_bomb else 0,
            "new_balance": float(new_balance),
            "packet_remaining_count": packet.total_count - packet.claimed_count,
            "packet_status": packet.status.value,
            "message": f"💣 踩雷！賠付 {penalty_amount}" if is_bomb else f"恭喜獲得 {amount} {packet.currency.value.upper()}"
        }
    )


@router.post("/wallet/transfer")
async def ai_transfer(
    request: AITransferRequest,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 代替用戶進行內部轉帳
    
    Headers:
    - Authorization: Bearer <API_KEY>
    - X-Telegram-User-Id: 123456789
    
    Body:
    {
        "to_user_id": 987654321,
        "currency": "usdt",
        "amount": 10.0,
        "note": "轉帳備註"
    }
    """
    from_tg_id, key_info = auth
    
    # 查找發送者
    result = await db.execute(select(User).where(User.tg_id == from_tg_id))
    from_user = result.scalar_one_or_none()
    
    if not from_user:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    # 查找接收者
    result = await db.execute(select(User).where(User.tg_id == request.to_user_id))
    to_user = result.scalar_one_or_none()
    
    if not to_user:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if from_user.id == to_user.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    
    # 映射幣種
    currency_map = {
        "usdt": CurrencyType.USDT,
        "ton": CurrencyType.TON,
        "stars": CurrencyType.STARS,
        "points": CurrencyType.POINTS,
    }
    currency = currency_map.get(request.currency.lower())
    if not currency:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {request.currency}")
    
    # 檢查餘額
    balance_field = f"balance_{currency.value}"
    from_balance = getattr(from_user, balance_field, 0) or Decimal(0)
    amount = Decimal(str(request.amount))
    
    if from_balance < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance: {from_balance} < {amount}"
        )
    
    # 執行轉帳
    to_balance = getattr(to_user, balance_field, 0) or Decimal(0)
    
    new_from_balance = from_balance - amount
    new_to_balance = to_balance + amount
    
    setattr(from_user, balance_field, new_from_balance)
    setattr(to_user, balance_field, new_to_balance)
    
    # 創建交易記錄
    tx_id = str(uuid.uuid4())
    
    from_tx = Transaction(
        user_id=from_user.id,
        type="transfer_out",
        currency=currency,
        amount=-amount,
        balance_before=from_balance,
        balance_after=new_from_balance,
        ref_id=tx_id,
        note=request.note or f"AI 轉帳給 {to_user.username or to_user.tg_id}",
        status="completed"
    )
    
    to_tx = Transaction(
        user_id=to_user.id,
        type="transfer_in",
        currency=currency,
        amount=amount,
        balance_before=to_balance,
        balance_after=new_to_balance,
        ref_id=tx_id,
        note=request.note or f"AI 轉帳來自 {from_user.username or from_user.tg_id}",
        status="completed"
    )
    
    db.add(from_tx)
    db.add(to_tx)
    await db.commit()
    
    logger.info(f"AI transfer: from={from_tg_id}, to={request.to_user_id}, amount={amount}")
    
    return AIResponse(
        success=True,
        data={
            "transaction_id": tx_id,
            "from_user_id": from_tg_id,
            "to_user_id": request.to_user_id,
            "currency": currency.value,
            "amount": float(amount),
            "from_balance_after": float(new_from_balance),
            "to_balance_after": float(new_to_balance),
            "message": f"成功轉帳 {amount} {currency.value.upper()}"
        }
    )


@router.get("/packets/{packet_uuid}")
async def ai_get_packet_info(
    packet_uuid: str,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    AI 獲取紅包詳情
    """
    tg_id, key_info = auth
    
    result = await db.execute(select(RedPacket).where(RedPacket.uuid == packet_uuid))
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")
    
    # 獲取發送者信息
    sender_result = await db.execute(select(User).where(User.id == packet.sender_id))
    sender = sender_result.scalar_one_or_none()
    
    # 獲取領取列表
    claims_result = await db.execute(
        select(RedPacketClaim).where(RedPacketClaim.red_packet_id == packet.id)
    )
    claims = claims_result.scalars().all()
    
    return AIResponse(
        success=True,
        data={
            "packet_uuid": packet.uuid,
            "sender": {
                "tg_id": sender.tg_id if sender else None,
                "username": sender.username if sender else None,
                "first_name": sender.first_name if sender else None,
            },
            "currency": packet.currency.value,
            "packet_type": packet.packet_type.value,
            "total_amount": float(packet.total_amount),
            "total_count": packet.total_count,
            "claimed_amount": float(packet.claimed_amount),
            "claimed_count": packet.claimed_count,
            "remaining_amount": float(packet.total_amount - packet.claimed_amount),
            "remaining_count": packet.total_count - packet.claimed_count,
            "message": packet.message,
            "bomb_number": packet.bomb_number,
            "status": packet.status.value,
            "created_at": packet.created_at.isoformat() if packet.created_at else None,
            "expires_at": packet.expires_at.isoformat() if packet.expires_at else None,
            "claims_count": len(claims)
        }
    )
