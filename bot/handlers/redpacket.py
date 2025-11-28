"""
Lucky Red - 紅包處理器
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from decimal import Decimal
import uuid
import random
from datetime import datetime, timedelta

from shared.config.settings import get_settings
from shared.database.connection import get_db
from shared.database.models import User, RedPacket, RedPacketClaim, CurrencyType, RedPacketType, RedPacketStatus

settings = get_settings()


async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /send 命令"""
    user = update.effective_user
    chat = update.effective_chat
    
    # 只能在群組中發紅包
    if chat.type == "private":
        await update.message.reply_text("請在群組中使用此命令發送紅包")
        return
    
    # 解析參數: /send <金額> <數量> [祝福語]
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "用法: /send <金額> <數量> [祝福語]\n"
            "例如: /send 10 5 恭喜發財"
        )
        return
    
    try:
        amount = Decimal(args[0])
        count = int(args[1])
        message = " ".join(args[2:]) if len(args) > 2 else "恭喜發財！🧧"
    except (ValueError, IndexError):
        await update.message.reply_text("參數格式錯誤，請輸入正確的金額和數量")
        return
    
    if amount <= 0 or count <= 0:
        await update.message.reply_text("金額和數量必須大於0")
        return
    
    if count > 100:
        await update.message.reply_text("每個紅包最多100份")
        return
    
    # 檢查餘額
    with get_db() as db:
        db_user = db.query(User).filter(User.tg_id == user.id).first()
        
        if not db_user:
            await update.message.reply_text("請先使用 /start 註冊")
            return
        
        if (db_user.balance_usdt or 0) < amount:
            await update.message.reply_text(f"餘額不足，當前 USDT 餘額: {float(db_user.balance_usdt or 0):.2f}")
            return
        
        # 扣除餘額
        db_user.balance_usdt = (db_user.balance_usdt or 0) - amount
        
        # 創建紅包
        packet = RedPacket(
            uuid=str(uuid.uuid4()),
            sender_id=db_user.id,
            chat_id=chat.id,
            chat_title=chat.title,
            currency=CurrencyType.USDT,
            packet_type=RedPacketType.RANDOM,
            total_amount=amount,
            total_count=count,
            message=message,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(packet)
        db.commit()
        db.refresh(packet)
        
        packet_uuid = packet.uuid
    
    # 發送紅包消息
    text = f"""
🧧 *{user.first_name} 發了一個紅包*

💰 {amount} USDT | 👥 {count} 份
📝 {message}

點擊下方按鈕搶紅包！
"""
    
    keyboard = [[InlineKeyboardButton("🧧 搶紅包", callback_data=f"claim:{packet_uuid}")]]
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理搶紅包回調"""
    query = update.callback_query
    user = query.from_user
    
    # 先快速響應 callback query，避免超時
    await query.answer("處理中...", cache_time=0)
    
    # 解析紅包 UUID
    try:
        packet_uuid = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await query.answer("無效的紅包鏈接", show_alert=True)
        return
    
    with get_db() as db:
        # 查找紅包
        packet = db.query(RedPacket).filter(RedPacket.uuid == packet_uuid).first()
        
        if not packet:
            await query.answer("紅包不存在", show_alert=True)
            return
        
        if packet.status != RedPacketStatus.ACTIVE:
            await query.answer("紅包已被搶完或已過期", show_alert=True)
            return
        
        if packet.expires_at and packet.expires_at < datetime.utcnow():
            packet.status = RedPacketStatus.EXPIRED
            db.commit()
            await query.answer("紅包已過期", show_alert=True)
            return
        
        # 查找用戶
        db_user = db.query(User).filter(User.tg_id == user.id).first()
        if not db_user:
            db_user = User(tg_id=user.id, username=user.username, first_name=user.first_name)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        # 檢查是否已領取
        existing = db.query(RedPacketClaim).filter(
            RedPacketClaim.red_packet_id == packet.id,
            RedPacketClaim.user_id == db_user.id
        ).first()
        
        if existing:
            # 獲取貨幣符號
            currency_symbol_map = {
                CurrencyType.USDT: "USDT",
                CurrencyType.TON: "TON",
                CurrencyType.STARS: "Stars",
                CurrencyType.POINTS: "Points",
            }
            currency_symbol = currency_symbol_map.get(packet.currency, "USDT")
            await query.answer(f"你已經領過了！獲得 {float(existing.amount):.4f} {currency_symbol}", show_alert=True)
            return
        
        # 計算金額
        remaining_amount = packet.total_amount - packet.claimed_amount
        remaining_count = packet.total_count - packet.claimed_count
        
        if remaining_count <= 0:
            packet.status = RedPacketStatus.COMPLETED
            db.commit()
            await query.answer("紅包已被搶完", show_alert=True)
            return
        
        if remaining_count == 1:
            claim_amount = remaining_amount
        else:
            max_amount = remaining_amount * Decimal("0.9") / remaining_count * 2
            claim_amount = Decimal(str(random.uniform(0.0001, float(max_amount))))
            claim_amount = min(claim_amount, remaining_amount - Decimal("0.0001") * (remaining_count - 1))
        
        claim_amount = round(claim_amount, 8)
        
        # 創建領取記錄
        claim = RedPacketClaim(
            red_packet_id=packet.id,
            user_id=db_user.id,
            amount=claim_amount,
        )
        db.add(claim)
        
        # 更新紅包
        packet.claimed_amount += claim_amount
        packet.claimed_count += 1
        
        if packet.claimed_count >= packet.total_count:
            packet.status = RedPacketStatus.COMPLETED
            packet.completed_at = datetime.utcnow()
        
        # 更新用戶餘額（根據貨幣類型）
        currency_field_map = {
            CurrencyType.USDT: "balance_usdt",
            CurrencyType.TON: "balance_ton",
            CurrencyType.STARS: "balance_stars",
            CurrencyType.POINTS: "balance_points",
        }
        balance_field = currency_field_map.get(packet.currency, "balance_usdt")
        current_balance = getattr(db_user, balance_field, 0) or 0
        setattr(db_user, balance_field, current_balance + claim_amount)
        
        db.commit()
        
        # 獲取發送者信息
        sender = db.query(User).filter(User.id == packet.sender_id).first()
        sender_name = sender.first_name if sender else "Unknown"
        
        # 在數據庫會話內讀取所有需要的屬性值
        total_amount = float(packet.total_amount)
        claimed_count = packet.claimed_count
        total_count = packet.total_count
        packet_message = packet.message
        packet_status = packet.status
        packet_uuid = packet.uuid
        packet_currency = packet.currency
        
        # 獲取貨幣符號
        currency_symbol_map = {
            CurrencyType.USDT: "USDT",
            CurrencyType.TON: "TON",
            CurrencyType.STARS: "Stars",
            CurrencyType.POINTS: "Points",
        }
        currency_symbol = currency_symbol_map.get(packet_currency, "USDT")
    
    await query.answer(f"🎉 恭喜獲得 {float(claim_amount):.4f} {currency_symbol}！", show_alert=True)
    
    # 更新消息（使用已保存的變量，而不是數據庫對象）
    text = f"""
🧧 *{sender_name} 發了一個紅包*

💰 {total_amount:.2f} {currency_symbol} | 👥 {claimed_count}/{total_count} 份
📝 {packet_message}

{user.first_name} 搶到了 {float(claim_amount):.4f} {currency_symbol}！
"""
    
    if packet_status == RedPacketStatus.COMPLETED:
        text += "\n✅ 紅包已搶完"
        keyboard = []
    else:
        keyboard = [[InlineKeyboardButton("🧧 搶紅包", callback_data=f"claim:{packet_uuid}")]]
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )

