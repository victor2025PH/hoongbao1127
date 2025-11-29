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
from telegram import Bot

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
    
    # 解析紅包 UUID
    try:
        packet_uuid = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await query.answer("無效的紅包鏈接", show_alert=True)
        return
    
    # 先快速檢查是否已領取（避免重複搶包時只顯示"處理中"）
    packet_id = None
    user_id = None
    with get_db() as db:
        # 查找紅包
        packet = db.query(RedPacket).filter(RedPacket.uuid == packet_uuid).first()
        
        if not packet:
            await query.answer("紅包不存在", show_alert=True)
            return
        
        # 在會話內保存 ID（避免 DetachedInstanceError）
        packet_id = packet.id
        packet_status_check = packet.status
        packet_expires_at = packet.expires_at
        packet_currency = packet.currency
        
        if packet_status_check != RedPacketStatus.ACTIVE:
            await query.answer("紅包已被搶完或已過期", show_alert=True)
            return
        
        if packet_expires_at and packet_expires_at < datetime.utcnow():
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
        
        # 在會話內保存 user_id
        user_id = db_user.id
        
        # 檢查是否已領取（在顯示"處理中"之前檢查）
        existing = db.query(RedPacketClaim).filter(
            RedPacketClaim.red_packet_id == packet_id,
            RedPacketClaim.user_id == user_id
        ).first()
        
        if existing:
            # 獲取貨幣符號
            currency_symbol_map = {
                CurrencyType.USDT: "USDT",
                CurrencyType.TON: "TON",
                CurrencyType.STARS: "Stars",
                CurrencyType.POINTS: "Points",
            }
            currency_symbol = currency_symbol_map.get(packet_currency, "USDT")
            await query.answer(f"你已經領過了！獲得 {float(existing.amount):.2f} {currency_symbol}", show_alert=True)
            return
    
    # 如果未領取，現在顯示"處理中"並繼續處理
    await query.answer("處理中...", cache_time=0)
    
    # 重新打開數據庫會話進行實際的搶包操作
    with get_db() as db:
        # 重新查詢 packet 和 db_user（避免 DetachedInstanceError）
        packet = db.query(RedPacket).filter(RedPacket.id == packet_id).first()
        db_user = db.query(User).filter(User.id == user_id).first()
        
        if not packet or not db_user:
            await query.answer("數據錯誤，請重試", show_alert=True)
            return
        
        # 再次檢查是否已領取（防止並發搶包）
        existing = db.query(RedPacketClaim).filter(
            RedPacketClaim.red_packet_id == packet.id,
            RedPacketClaim.user_id == db_user.id
        ).first()
        
        if existing:
            currency_symbol_map = {
                CurrencyType.USDT: "USDT",
                CurrencyType.TON: "TON",
                CurrencyType.STARS: "Stars",
                CurrencyType.POINTS: "Points",
            }
            currency_symbol = currency_symbol_map.get(packet.currency, "USDT")
            await query.answer(f"你已經領過了！獲得 {float(existing.amount):.2f} {currency_symbol}", show_alert=True)
            return
        
        # 計算金額
        remaining_amount = packet.total_amount - packet.claimed_amount
        remaining_count = packet.total_count - packet.claimed_count
        
        if remaining_count <= 0:
            packet.status = RedPacketStatus.COMPLETED
            db.commit()
            await query.answer("紅包已被搶完", show_alert=True)
            return
        
        # 根據紅包類型計算金額（保留兩位小數）
        if packet.packet_type == RedPacketType.EQUAL:  # 紅包炸彈（需要隨機金額以便檢測炸彈）
            # 炸彈紅包也需要隨機金額，但總和必須等於總金額
            # 最後一個包直接取剩餘金額，其他包隨機分配
            if remaining_count == 1:
                # 最後一份直接取剩餘金額，確保至少 0.01
                claim_amount = max(remaining_amount, Decimal("0.01"))
                claim_amount = round(claim_amount, 2)  # 保留兩位小數
                # 如果四捨五入後為 0，確保至少 0.01
                if claim_amount <= 0:
                    claim_amount = Decimal("0.01")
            else:
                # 計算平均金額
                avg_amount = remaining_amount / Decimal(str(remaining_count))
                # 隨機範圍：平均金額的 50% 到 150%
                min_amount = avg_amount * Decimal("0.5")
                max_amount = avg_amount * Decimal("1.5")
                # 確保不會超過剩餘金額，且為其他包留出至少 0.01
                max_amount = min(max_amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
                # 確保 max_amount 至少等於 min_amount
                if max_amount < min_amount:
                    max_amount = min_amount
                # 生成隨機金額
                claim_amount = Decimal(str(random.uniform(float(min_amount), float(max_amount))))
                # 確保至少 0.01
                claim_amount = max(claim_amount, Decimal("0.01"))
                # 確保不超過剩餘金額
                claim_amount = min(claim_amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
                claim_amount = round(claim_amount, 2)  # 保留兩位小數
        else:  # 手氣最佳（隨機金額）
            if remaining_count == 1:
                # 最後一份直接取剩餘金額，確保至少 0.01
                claim_amount = max(remaining_amount, Decimal("0.01"))
                claim_amount = round(claim_amount, 2)  # 保留兩位小數
                # 如果四捨五入後為 0，確保至少 0.01
                if claim_amount <= 0:
                    claim_amount = Decimal("0.01")
            else:
                max_amount = remaining_amount * Decimal("0.9") / remaining_count * 2
                claim_amount = Decimal(str(random.uniform(0.01, float(max_amount))))  # 最小 0.01
                claim_amount = min(claim_amount, remaining_amount - Decimal("0.01") * (remaining_count - 1))
                claim_amount = round(claim_amount, 2)  # 保留兩位小數
        
        # 獲取貨幣符號映射（提前定義，用於錯誤提示）
        currency_symbol_map = {
            CurrencyType.USDT: "USDT",
            CurrencyType.TON: "TON",
            CurrencyType.STARS: "Stars",
            CurrencyType.POINTS: "Points",
        }
        
        # 檢查是否踩雷（僅紅包炸彈）
        is_bomb = False
        penalty_amount = None
        if packet.packet_type == RedPacketType.EQUAL and packet.bomb_number is not None:
            # 獲取金額的最後一位小數（兩位小數）
            amount_str = f"{float(claim_amount):.2f}"
            # 找到最後一個數字（小數點後第二位）
            last_digit = None
            if '.' in amount_str:
                decimal_part = amount_str.split('.')[1]
                if len(decimal_part) >= 2:
                    last_digit = int(decimal_part[1])  # 小數點後第二位
                elif len(decimal_part) == 1:
                    last_digit = int(decimal_part[0])  # 小數點後第一位
            else:
                # 如果沒有小數點，取個位數
                last_digit = int(amount_str[-1])
            
            # 如果最後一位數字等於炸彈數字，則踩雷
            if last_digit == packet.bomb_number:
                is_bomb = True
                
                # 計算賠付金額
                # 單雷（10個包）：賠付全額
                # 雙雷（5個包）：賠付雙倍
                if packet.total_count == 10:  # 單雷
                    penalty_amount = packet.total_amount
                else:  # 雙雷（5個包）
                    penalty_amount = packet.total_amount * Decimal("2")
                
                # 檢查用戶餘額是否足夠賠付
                currency_field_map = {
                    CurrencyType.USDT: "balance_usdt",
                    CurrencyType.TON: "balance_ton",
                    CurrencyType.STARS: "balance_stars",
                    CurrencyType.POINTS: "balance_points",
                }
                balance_field = currency_field_map.get(packet.currency, "balance_usdt")
                current_balance = getattr(db_user, balance_field, 0) or Decimal(0)
                
                if current_balance < penalty_amount:
                    currency_symbol = currency_symbol_map.get(packet.currency, "USDT")
                    await query.answer(
                        f"⚠️ 餘額不足！需要 {float(penalty_amount):.2f} {currency_symbol} 才能參與搶紅包（可能踩雷需賠付）",
                        show_alert=True
                    )
                    return
        
        # 創建領取記錄
        claim = RedPacketClaim(
            red_packet_id=packet.id,
            user_id=db_user.id,
            amount=claim_amount,
            is_bomb=is_bomb,
            penalty_amount=penalty_amount if is_bomb else None,
        )
        db.add(claim)
        
        # 更新紅包
        packet.claimed_amount += claim_amount
        packet.claimed_count += 1
        
        # 標記最佳手氣（僅手氣最佳類型，當紅包搶完時）
        is_luckiest = False
        if packet.packet_type == RedPacketType.RANDOM and packet.claimed_count >= packet.total_count:
            # 查找所有搶包記錄（包括剛創建的），找出金額最大的
            all_existing_claims = db.query(RedPacketClaim).filter(
                RedPacketClaim.red_packet_id == packet.id
            ).all()
            
            # 找到金額最大的記錄
            max_amount = Decimal(0)
            luckiest_claim_id = None
            for existing_claim in all_existing_claims:
                if existing_claim.amount > max_amount:
                    max_amount = existing_claim.amount
                    luckiest_claim_id = existing_claim.id
            
            # 標記最佳手氣（清除之前的標記，設置新的）
            if luckiest_claim_id:
                # 清除所有記錄的最佳手氣標記
                for existing_claim in all_existing_claims:
                    existing_claim.is_luckiest = False
                # 設置新的最佳手氣
                luckiest_claim = db.query(RedPacketClaim).filter(RedPacketClaim.id == luckiest_claim_id).first()
                if luckiest_claim:
                    luckiest_claim.is_luckiest = True
                    # 如果當前用戶是最佳手氣
                    if luckiest_claim.id == claim.id:
                        is_luckiest = True
        
        # 保存是否剛完成（用於發送提醒消息）
        just_completed = False
        if packet.claimed_count >= packet.total_count:
            if packet.status != RedPacketStatus.COMPLETED:
                just_completed = True
            packet.status = RedPacketStatus.COMPLETED
            packet.completed_at = datetime.utcnow()
        
        # 保存 is_luckiest 到變量（在會話內）
        is_luckiest_value = is_luckiest
        
        # 保存是否剛完成和最佳手氣用戶信息（用於發送提醒消息）
        just_completed_value = just_completed
        luckiest_user_tg_id = None
        luckiest_user_name = None
        if just_completed_value:
            if packet.packet_type == RedPacketType.RANDOM:
                # 手氣最佳：找到最佳手氣用戶
                luckiest_claim = db.query(RedPacketClaim).filter(
                    RedPacketClaim.red_packet_id == packet.id,
                    RedPacketClaim.is_luckiest == True
                ).first()
                if luckiest_claim:
                    luckiest_user = db.query(User).filter(User.id == luckiest_claim.user_id).first()
                    if luckiest_user:
                        luckiest_user_tg_id = luckiest_user.tg_id
                        luckiest_user_name = luckiest_user.first_name or '用戶'
            elif packet.packet_type == RedPacketType.EQUAL:
                # 炸彈紅包：找到贏最多的人（金額最大的，排除踩雷的）
                all_claims_for_winner = db.query(RedPacketClaim).filter(
                    RedPacketClaim.red_packet_id == packet.id
                ).all()
                max_net_amount = Decimal("-999999")
                winner_user_id = None
                for claim_record in all_claims_for_winner:
                    net_amount = claim_record.amount
                    if claim_record.is_bomb and claim_record.penalty_amount:
                        net_amount = net_amount - claim_record.penalty_amount
                    if net_amount > max_net_amount:
                        max_net_amount = net_amount
                        winner_user_id = claim_record.user_id
                if winner_user_id:
                    winner_user = db.query(User).filter(User.id == winner_user_id).first()
                    if winner_user:
                        luckiest_user_tg_id = winner_user.tg_id
                        luckiest_user_name = winner_user.first_name or '用戶'
        
        # 更新用戶餘額（根據貨幣類型）
        currency_field_map = {
            CurrencyType.USDT: "balance_usdt",
            CurrencyType.TON: "balance_ton",
            CurrencyType.STARS: "balance_stars",
            CurrencyType.POINTS: "balance_points",
        }
        balance_field = currency_field_map.get(packet.currency, "balance_usdt")
        current_balance = getattr(db_user, balance_field, 0) or Decimal(0)
        
        if is_bomb:
            # 踩雷：扣除賠付金額（金額退回紅包池，用戶需要賠付）
            # 用戶獲得 claim_amount，但需要賠付 penalty_amount
            # 實際餘額變化：claim_amount - penalty_amount（通常是負數）
            net_change = claim_amount - penalty_amount
            setattr(db_user, balance_field, current_balance + net_change)
            
            # 發送者獲得賠付金額
            sender = db.query(User).filter(User.id == packet.sender_id).first()
            if sender:
                sender_balance = getattr(sender, balance_field, 0) or Decimal(0)
                setattr(sender, balance_field, sender_balance + penalty_amount)
        else:
            # 正常領取：增加餘額
            setattr(db_user, balance_field, current_balance + claim_amount)
        
        db.commit()
        
        # 獲取發送者信息
        sender = db.query(User).filter(User.id == packet.sender_id).first()
        sender_name = sender.first_name if sender else "Unknown"
        
        # 在數據庫會話內讀取所有需要的屬性值
        packet_id = packet.id  # 保存 packet.id，避免 DetachedInstanceError
        total_amount = float(packet.total_amount)
        claimed_count = packet.claimed_count
        total_count = packet.total_count
        packet_message = packet.message
        packet_status = packet.status
        packet_uuid = packet.uuid
        packet_currency = packet.currency
        packet_bomb_number = packet.bomb_number
        packet_type = packet.packet_type
        
        # 獲取貨幣符號
        currency_symbol_map = {
            CurrencyType.USDT: "USDT",
            CurrencyType.TON: "TON",
            CurrencyType.STARS: "Stars",
            CurrencyType.POINTS: "Points",
        }
        currency_symbol = currency_symbol_map.get(packet_currency, "USDT")
        
        # 檢查是否踩雷（從 claim 記錄中讀取）
        is_bomb_value = claim.is_bomb if hasattr(claim, 'is_bomb') else False
        penalty_amount_value = claim.penalty_amount if hasattr(claim, 'penalty_amount') and claim.penalty_amount else None
        
        # 保存 is_luckiest（在會話內讀取）
        is_luckiest_value = is_luckiest
        
        # 獲取所有已搶紅包的記錄（在同一個會話中查詢，避免 DetachedInstanceError）
        all_claims = db.query(RedPacketClaim).filter(
            RedPacketClaim.red_packet_id == packet_id
        ).order_by(RedPacketClaim.claimed_at.asc()).all()
        
        # 獲取所有搶包用戶的信息（在數據庫會話內讀取所有屬性）
        claimers_info = []
        for claim_record in all_claims:
            # 在會話內讀取所有需要的屬性值
            claim_user_id = claim_record.user_id
            claim_amount = float(claim_record.amount)
            claim_is_bomb = claim_record.is_bomb if hasattr(claim_record, 'is_bomb') else False
            claim_penalty = float(claim_record.penalty_amount) if hasattr(claim_record, 'penalty_amount') and claim_record.penalty_amount else None
            claim_is_luckiest = claim_record.is_luckiest if hasattr(claim_record, 'is_luckiest') else False
            
            # 查詢用戶信息
            claimer_user = db.query(User).filter(User.id == claim_user_id).first()
            if claimer_user:
                claimer_name = claimer_user.first_name or '用戶'
                claimers_info.append({
                    'name': claimer_name,
                    'amount': claim_amount,
                    'is_bomb': claim_is_bomb,
                    'penalty': claim_penalty,
                    'is_luckiest': claim_is_luckiest,
                })
        
        # 按金額排序（用於排行榜顯示）
        claimers_info_sorted = sorted(claimers_info, key=lambda x: x['amount'], reverse=True)
    
    # 根據是否踩雷和是否最佳手氣顯示不同的提示
    if is_bomb_value and penalty_amount_value:
        thunder_type = "單雷" if total_count == 10 else "雙雷"
        alert_text = f"💣 踩雷了！需要賠付 {float(penalty_amount_value):.2f} {currency_symbol}（{thunder_type}）"
    elif is_luckiest_value and packet_status == RedPacketStatus.COMPLETED:
        alert_text = f"🎉 恭喜獲得 {float(claim_amount):.2f} {currency_symbol}！\n🏆 你是最佳手氣！"
    else:
        alert_text = f"🎉 恭喜獲得 {float(claim_amount):.2f} {currency_symbol}！"
    
    # 確保彈窗提示始終顯示（無論什麼情況）
    try:
        await query.answer(alert_text, show_alert=True)
    except Exception as e:
        logger.error(f"Failed to show alert: {e}")
        # 如果彈窗失敗，至少嘗試簡單的 answer
        try:
            await query.answer("處理完成", show_alert=False)
        except:
            pass
    
    # 更新消息（使用已保存的變量，而不是數據庫對象）
    text = f"""
🧧 *{sender_name} 發了一個紅包*

💰 {total_amount:.2f} {currency_symbol} | 👥 {claimed_count}/{total_count} 份
"""
    
    # 如果是紅包炸彈，顯示炸彈信息
    if packet_type == RedPacketType.EQUAL and packet_bomb_number is not None:
        thunder_type = "單雷" if total_count == 10 else "雙雷"
        text += f"💣 炸彈數字: {packet_bomb_number} | {thunder_type}\n"
    
    text += f"📝 {packet_message}\n\n"
    
    # 顯示所有已搶紅包的用戶和金額（排行榜，按金額排序）
    if claimers_info_sorted:
        text += "📊 搶包排行榜：\n"
        for idx, claimer in enumerate(claimers_info_sorted, 1):
            # 構建顯示文本
            rank_icon = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            name_text = claimer['name']
            
            # 添加最佳手氣標記（僅手氣最佳類型且已搶完）
            if claimer['is_luckiest'] and packet_type == RedPacketType.RANDOM and packet_status == RedPacketStatus.COMPLETED:
                name_text = f"🏆 {name_text} (最佳手氣)"
            
            # 添加踩雷標記
            if claimer['is_bomb'] and claimer['penalty']:
                text += f"{rank_icon} {name_text} 搶到了 {claimer['amount']:.2f} {currency_symbol}，💣 踩雷了！需賠付 {claimer['penalty']:.2f} {currency_symbol}\n"
            else:
                text += f"{rank_icon} {name_text} 搶到了 {claimer['amount']:.2f} {currency_symbol}！\n"
        text += "\n"
        
        # 如果紅包已搶完且是手氣最佳類型，顯示最佳手氣提示
        if packet_status == RedPacketStatus.COMPLETED and packet_type == RedPacketType.RANDOM:
            luckiest_claimer = next((c for c in claimers_info_sorted if c['is_luckiest']), None)
            if luckiest_claimer:
                text += f"🏆 *{luckiest_claimer['name']}* 是本次最佳手氣！\n"
    
    if packet_status == RedPacketStatus.COMPLETED:
        text += "✅ 紅包已搶完"
        keyboard = []
    else:
        remaining = total_count - claimed_count
        keyboard = [[InlineKeyboardButton(f"🧧 搶紅包 ({remaining} 份剩餘)", callback_data=f"claim:{packet_uuid}")]]
    
    # 更新群組消息
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        )
        logger.info(f"Red packet message updated successfully for packet {packet_uuid}, claimed: {claimed_count}/{total_count}")
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        # 如果編輯失敗，至少確保用戶收到了提示
        # 嘗試發送新消息作為備用
        try:
            if query.message and query.message.chat:
                await query.message.reply_text(
                    f"🎉 {user.first_name} 搶到了 {float(claim_amount):.2f} {currency_symbol}！",
                    parse_mode="Markdown"
                )
        except Exception as e2:
            logger.error(f"Failed to send backup message: {e2}")
    
    # 如果紅包剛完成，發送提醒消息給下一個發送者
    if just_completed_value and luckiest_user_tg_id and query.message and query.message.chat:
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            
            # 構建提醒消息
            reminder_text = ""
            if packet_type == RedPacketType.RANDOM:
                # 手氣最佳提醒
                reminder_text = f"""🎉 *恭喜 {luckiest_user_name} 成為最佳手氣！*

📢 *請發送下一個紅包*
💰 金額：{total_amount:.2f} {currency_symbol}
👥 數量：{total_count} 份
🎮 類型：手氣最佳
📝 祝福語：{packet_message}

💡 提示：您可以使用 miniapp 或 /send 命令發送紅包"""
            elif packet_type == RedPacketType.EQUAL and packet_bomb_number is not None:
                # 炸彈紅包提醒
                thunder_type = "單雷" if total_count == 10 else "雙雷"
                reminder_text = f"""💣 *恭喜 {luckiest_user_name} 贏得最多！*

📢 *請發送下一個紅包炸彈*
💰 金額：{total_amount:.2f} {currency_symbol}
👥 數量：{total_count} 份（{thunder_type}）
💣 炸彈數字：{packet_bomb_number}
📝 祝福語：{packet_message}

💡 提示：您可以使用 miniapp 或 /send 命令發送紅包"""
            
            if reminder_text:
                await bot.send_message(
                    chat_id=query.message.chat.id,
                    text=reminder_text,
                    parse_mode="Markdown",
                    reply_to_message_id=query.message.message_id
                )
                logger.info(f"Reminder message sent to {luckiest_user_name} (tg_id: {luckiest_user_tg_id}) for next red packet")
        except Exception as e:
            logger.error(f"Failed to send reminder message: {e}")

