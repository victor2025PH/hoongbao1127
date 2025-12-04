"""
Lucky Red - AI 系統對接 API（完整版）
允許外部 AI 聊天系統調用紅包遊戲功能

功能列表：
- 健康檢查、餘額查詢、用戶資料
- 發送紅包、領取紅包、紅包詳情
- 內部轉帳、交易記錄
- 每日簽到、排行榜
- 紅包列表（發送/領取歷史）

文件路徑：/opt/luckyred/api/routers/ai_api.py
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
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
    packet_type: str = Field(default="random", description="類型: random(手氣), equal(均分/炸彈)")
    total_amount: float = Field(..., gt=0, description="總金額")
    total_count: int = Field(..., ge=1, le=100, description="份數")
    message: str = Field(default="🤖 AI 紅包", max_length=256, description="祝福語")
    chat_id: Optional[int] = Field(None, description="目標群組 ID（可選）")
    bomb_number: Optional[int] = Field(None, ge=0, le=9, description="炸彈數字 0-9（炸彈紅包）")


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

async def verify_ai_api_key(
    authorization: str = Header(..., description="Bearer <API_KEY>"),
    x_telegram_user_id: int = Header(..., alias="X-Telegram-User-Id"),
    x_ai_system_id: str = Header(None, alias="X-AI-System-Id"),
    db: AsyncSession = Depends(get_db_session)
) -> tuple[int, dict]:
    """驗證 AI 系統 API Key"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    api_key = authorization[7:]
    expected_key = getattr(settings, 'AI_API_KEY', None)
    
    if not expected_key:
        logger.warning("AI API Key not configured, allowing any key in dev mode")
        if not getattr(settings, 'DEBUG', False):
            raise HTTPException(status_code=401, detail="AI API not configured")
    elif api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = await db.execute(select(User).where(User.tg_id == x_telegram_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {x_telegram_user_id} not found")
    
    if getattr(user, 'is_banned', False):
        raise HTTPException(status_code=403, detail="User is banned")
    
    logger.info(f"AI API: system={x_ai_system_id}, user={x_telegram_user_id}")
    
    return x_telegram_user_id, {"system_id": x_ai_system_id, "user_db_id": user.id}


# ============================================================
# 基礎端點
# ============================================================

@router.get("/status")
async def ai_api_status():
    """AI API 健康檢查（無需認證）"""
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
                "GET /api/v2/ai/packets/{uuid}",
                "GET /api/v2/ai/packets/list",
                "POST /api/v2/ai/wallet/transfer",
                "GET /api/v2/ai/transactions",
                "POST /api/v2/ai/checkin",
                "GET /api/v2/ai/leaderboard",
            ]
        }
    )


@router.get("/wallet/balance")
async def ai_get_balance(
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """查詢用戶餘額"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usdt = float(user.balance_usdt or 0)
    ton = float(user.balance_ton or 0)
    stars = user.balance_stars or 0
    points = user.balance_points or 0
    total_usdt = usdt + ton * 5.0 + stars * 0.01 + points * 0.001
    
    return AIResponse(
        success=True,
        data={
            "user_id": tg_id,
            "balances": {"usdt": usdt, "ton": ton, "stars": stars, "points": points},
            "total_usdt_equivalent": round(total_usdt, 2)
        }
    )


@router.get("/user/profile")
async def ai_get_user_profile(
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取用戶資料及統計"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 統計紅包數據
    sent_result = await db.execute(select(RedPacket).where(RedPacket.sender_id == user.id))
    sent_packets = sent_result.scalars().all()
    
    claim_result = await db.execute(select(RedPacketClaim).where(RedPacketClaim.user_id == user.id))
    claims = claim_result.scalars().all()
    
    return AIResponse(
        success=True,
        data={
            "user_id": tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": getattr(user, 'last_name', None),
            "level": getattr(user, 'level', 1) or 1,
            "xp": getattr(user, 'xp', 0) or 0,
            "invite_code": getattr(user, 'invite_code', None),
            "invite_count": getattr(user, 'invite_count', 0) or 0,
            "stats": {
                "packets_sent": len(sent_packets),
                "packets_claimed": len(claims),
                "total_sent_amount": float(sum(p.total_amount for p in sent_packets)),
                "total_claimed_amount": float(sum(c.amount for c in claims)),
            },
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )


# ============================================================
# 紅包功能
# ============================================================

@router.post("/packets/send")
async def ai_send_packet(
    request: AIPacketSendRequest,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """發送紅包"""
    tg_id, _ = auth
    
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
    packet_type_map = {"random": RedPacketType.RANDOM, "equal": RedPacketType.EQUAL}
    packet_type = packet_type_map.get(request.packet_type.lower())
    if not packet_type:
        raise HTTPException(status_code=400, detail=f"Invalid packet_type: {request.packet_type}")
    
    # 炸彈紅包驗證
    bomb_number = None
    if request.bomb_number is not None:
        if request.total_count not in [5, 10]:
            raise HTTPException(status_code=400, detail="Bomb packet count must be 5 or 10")
        bomb_number = request.bomb_number
        packet_type = RedPacketType.EQUAL  # 炸彈紅包使用均分
    
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
        bomb_number=bomb_number,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    
    db.add(packet)
    await db.commit()
    await db.refresh(packet)
    
    logger.info(f"AI packet created: uuid={packet.uuid}, sender={tg_id}, amount={amount}")
    
    bot_username = getattr(settings, 'BOT_USERNAME', 'luckyred_bot')
    miniapp_url = getattr(settings, 'MINIAPP_URL', 'https://mini.usdt2026.cc')
    
    return AIResponse(
        success=True,
        data={
            "packet_id": packet.uuid,
            "packet_type": packet.packet_type.value,
            "is_bomb": bomb_number is not None,
            "bomb_number": bomb_number,
            "total_amount": float(packet.total_amount),
            "total_count": packet.total_count,
            "currency": packet.currency.value,
            "message": packet.message,
            "share_url": f"https://t.me/{bot_username}/app?startapp=p_{packet.uuid}",
            "deep_link": f"{miniapp_url}/packets/{packet.uuid}",
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
    """領取紅包"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    claimer = result.scalar_one_or_none()
    
    if not claimer:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(RedPacket).where(RedPacket.uuid == request.packet_uuid))
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")
    
    if packet.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Packet status: {packet.status.value}")
    
    if packet.expires_at and packet.expires_at < datetime.utcnow():
        packet.status = RedPacketStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Packet expired")
    
    # 檢查是否已領取
    result = await db.execute(
        select(RedPacketClaim).where(
            and_(RedPacketClaim.red_packet_id == packet.id, RedPacketClaim.user_id == claimer.id)
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
    
    if packet.bomb_number is not None:
        amount_str = f"{amount:.8f}"
        last_digit = int(amount_str[-1])
        
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
    
    if packet.claimed_count >= packet.total_count:
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
    
    logger.info(f"AI claimed: uuid={request.packet_uuid}, claimer={tg_id}, amount={amount}, bomb={is_bomb}")
    
    return AIResponse(
        success=True,
        data={
            "packet_uuid": packet.uuid,
            "claimed_amount": float(amount),
            "actual_amount": float(amount - penalty_amount) if is_bomb else float(amount),
            "is_bomb": is_bomb,
            "bomb_number": packet.bomb_number,
            "penalty_amount": float(penalty_amount) if is_bomb else 0,
            "new_balance": float(new_balance),
            "packet_remaining_count": packet.total_count - packet.claimed_count,
            "packet_status": packet.status.value,
            "message": f"💣 踩雷！賠付 {penalty_amount}" if is_bomb else f"🎉 獲得 {amount} {packet.currency.value.upper()}"
        }
    )


@router.get("/packets/{packet_uuid}")
async def ai_get_packet_info(
    packet_uuid: str,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取紅包詳情"""
    tg_id, _ = auth
    
    result = await db.execute(select(RedPacket).where(RedPacket.uuid == packet_uuid))
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")
    
    sender_result = await db.execute(select(User).where(User.id == packet.sender_id))
    sender = sender_result.scalar_one_or_none()
    
    claims_result = await db.execute(
        select(RedPacketClaim).where(RedPacketClaim.red_packet_id == packet.id)
    )
    claims = claims_result.scalars().all()
    
    # 檢查當前用戶是否已領取
    user_result = await db.execute(select(User).where(User.tg_id == tg_id))
    current_user = user_result.scalar_one_or_none()
    user_claimed = any(c.user_id == current_user.id for c in claims) if current_user else False
    
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
            "is_bomb": packet.bomb_number is not None,
            "bomb_number": packet.bomb_number,
            "total_amount": float(packet.total_amount),
            "total_count": packet.total_count,
            "claimed_amount": float(packet.claimed_amount),
            "claimed_count": packet.claimed_count,
            "remaining_amount": float(packet.total_amount - packet.claimed_amount),
            "remaining_count": packet.total_count - packet.claimed_count,
            "message": packet.message,
            "status": packet.status.value,
            "user_claimed": user_claimed,
            "created_at": packet.created_at.isoformat() if packet.created_at else None,
            "expires_at": packet.expires_at.isoformat() if packet.expires_at else None,
        }
    )


@router.get("/packets/list")
async def ai_get_packets_list(
    type: str = Query("sent", description="sent=發送的, claimed=領取的"),
    limit: int = Query(20, ge=1, le=100),
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取紅包列表"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if type == "sent":
        packets_result = await db.execute(
            select(RedPacket)
            .where(RedPacket.sender_id == user.id)
            .order_by(desc(RedPacket.created_at))
            .limit(limit)
        )
        packets = packets_result.scalars().all()
        
        return AIResponse(
            success=True,
            data={
                "type": "sent",
                "count": len(packets),
                "packets": [
                    {
                        "uuid": p.uuid,
                        "currency": p.currency.value,
                        "total_amount": float(p.total_amount),
                        "total_count": p.total_count,
                        "claimed_count": p.claimed_count,
                        "status": p.status.value,
                        "is_bomb": p.bomb_number is not None,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in packets
                ]
            }
        )
    else:
        claims_result = await db.execute(
            select(RedPacketClaim)
            .where(RedPacketClaim.user_id == user.id)
            .order_by(desc(RedPacketClaim.claimed_at))
            .limit(limit)
        )
        claims = claims_result.scalars().all()
        
        return AIResponse(
            success=True,
            data={
                "type": "claimed",
                "count": len(claims),
                "claims": [
                    {
                        "packet_id": c.red_packet_id,
                        "amount": float(c.amount),
                        "is_bomb": c.is_bomb,
                        "penalty_amount": float(c.penalty_amount) if c.penalty_amount else 0,
                        "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
                    }
                    for c in claims
                ]
            }
        )


# ============================================================
# 轉帳功能
# ============================================================

@router.post("/wallet/transfer")
async def ai_transfer(
    request: AITransferRequest,
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """內部轉帳"""
    from_tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == from_tg_id))
    from_user = result.scalar_one_or_none()
    
    if not from_user:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    result = await db.execute(select(User).where(User.tg_id == request.to_user_id))
    to_user = result.scalar_one_or_none()
    
    if not to_user:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if from_user.id == to_user.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    
    currency_map = {
        "usdt": CurrencyType.USDT,
        "ton": CurrencyType.TON,
        "stars": CurrencyType.STARS,
        "points": CurrencyType.POINTS,
    }
    currency = currency_map.get(request.currency.lower())
    if not currency:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {request.currency}")
    
    balance_field = f"balance_{currency.value}"
    from_balance = getattr(from_user, balance_field, 0) or Decimal(0)
    amount = Decimal(str(request.amount))
    
    if from_balance < amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance: {from_balance} < {amount}")
    
    to_balance = getattr(to_user, balance_field, 0) or Decimal(0)
    
    new_from = from_balance - amount
    new_to = to_balance + amount
    
    setattr(from_user, balance_field, new_from)
    setattr(to_user, balance_field, new_to)
    
    tx_id = str(uuid.uuid4())
    
    from_tx = Transaction(
        user_id=from_user.id, type="transfer_out", currency=currency,
        amount=-amount, balance_before=from_balance, balance_after=new_from,
        ref_id=tx_id, note=request.note or f"轉帳給 {to_user.username or to_user.tg_id}",
        status="completed"
    )
    to_tx = Transaction(
        user_id=to_user.id, type="transfer_in", currency=currency,
        amount=amount, balance_before=to_balance, balance_after=new_to,
        ref_id=tx_id, note=request.note or f"來自 {from_user.username or from_user.tg_id}",
        status="completed"
    )
    
    db.add(from_tx)
    db.add(to_tx)
    await db.commit()
    
    logger.info(f"AI transfer: {from_tg_id} -> {request.to_user_id}, {amount} {currency.value}")
    
    return AIResponse(
        success=True,
        data={
            "transaction_id": tx_id,
            "from_user_id": from_tg_id,
            "to_user_id": request.to_user_id,
            "currency": currency.value,
            "amount": float(amount),
            "from_balance_after": float(new_from),
            "message": f"成功轉帳 {amount} {currency.value.upper()}"
        }
    )


# ============================================================
# 交易記錄
# ============================================================

@router.get("/transactions")
async def ai_get_transactions(
    limit: int = Query(20, ge=1, le=100),
    currency: str = Query(None, description="篩選幣種"),
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取交易記錄"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = select(Transaction).where(Transaction.user_id == user.id)
    
    if currency:
        currency_map = {"usdt": CurrencyType.USDT, "ton": CurrencyType.TON, "stars": CurrencyType.STARS, "points": CurrencyType.POINTS}
        if currency.lower() in currency_map:
            query = query.where(Transaction.currency == currency_map[currency.lower()])
    
    query = query.order_by(desc(Transaction.created_at)).limit(limit)
    
    tx_result = await db.execute(query)
    transactions = tx_result.scalars().all()
    
    return AIResponse(
        success=True,
        data={
            "count": len(transactions),
            "transactions": [
                {
                    "id": tx.id,
                    "type": tx.type,
                    "currency": tx.currency.value,
                    "amount": float(tx.amount),
                    "balance_after": float(tx.balance_after),
                    "note": tx.note,
                    "status": tx.status,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                }
                for tx in transactions
            ]
        }
    )


# ============================================================
# 每日簽到
# ============================================================

@router.post("/checkin")
async def ai_checkin(
    auth: tuple = Depends(verify_ai_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """每日簽到"""
    tg_id, _ = auth
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = datetime.utcnow().date()
    last_checkin = getattr(user, 'last_checkin', None)
    
    if last_checkin and last_checkin.date() == today:
        return AIResponse(
            success=False,
            error={"code": "ALREADY_CHECKIN", "message": "今日已簽到"}
        )
    
    # 計算連續簽到
    streak = getattr(user, 'checkin_streak', 0) or 0
    if last_checkin and (today - last_checkin.date()).days == 1:
        streak += 1
    else:
        streak = 1
    
    # 獎勵：基礎 1 點 + 連續天數獎勵
    reward_points = min(1 + streak, 10)
    
    user.last_checkin = datetime.utcnow()
    user.checkin_streak = streak
    user.balance_points = (user.balance_points or 0) + reward_points
    
    await db.commit()
    
    return AIResponse(
        success=True,
        data={
            "checkin_date": today.isoformat(),
            "streak": streak,
            "reward_points": reward_points,
            "total_points": user.balance_points,
            "message": f"簽到成功！連續 {streak} 天，獲得 {reward_points} 積分"
        }
    )


# ============================================================
# 排行榜
# ============================================================

@router.get("/leaderboard")
async def ai_get_leaderboard(
    type: str = Query("balance", description="balance=餘額, packets=紅包數, claims=領取數"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取排行榜（無需認證）"""
    
    if type == "balance":
        result = await db.execute(
            select(User)
            .where(User.is_banned == False)
            .order_by(desc(User.balance_usdt))
            .limit(limit)
        )
        users = result.scalars().all()
        
        return AIResponse(
            success=True,
            data={
                "type": "balance",
                "leaderboard": [
                    {
                        "rank": i + 1,
                        "username": u.username or f"User_{u.tg_id}",
                        "first_name": u.first_name,
                        "balance_usdt": float(u.balance_usdt or 0),
                    }
                    for i, u in enumerate(users)
                ]
            }
        )
    
    elif type == "packets":
        result = await db.execute(
            select(User.id, User.username, User.first_name, func.count(RedPacket.id).label('count'))
            .join(RedPacket, RedPacket.sender_id == User.id)
            .group_by(User.id)
            .order_by(desc('count'))
            .limit(limit)
        )
        rows = result.all()
        
        return AIResponse(
            success=True,
            data={
                "type": "packets_sent",
                "leaderboard": [
                    {"rank": i + 1, "username": r.username, "first_name": r.first_name, "packets_sent": r.count}
                    for i, r in enumerate(rows)
                ]
            }
        )
    
    else:
        result = await db.execute(
            select(User.id, User.username, User.first_name, func.count(RedPacketClaim.id).label('count'))
            .join(RedPacketClaim, RedPacketClaim.user_id == User.id)
            .group_by(User.id)
            .order_by(desc('count'))
            .limit(limit)
        )
        rows = result.all()
        
        return AIResponse(
            success=True,
            data={
                "type": "packets_claimed",
                "leaderboard": [
                    {"rank": i + 1, "username": r.username, "first_name": r.first_name, "packets_claimed": r.count}
                    for i, r in enumerate(rows)
                ]
            }
        )
