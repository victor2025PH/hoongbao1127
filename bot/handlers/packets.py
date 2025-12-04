"""
Lucky Red - 紅包處理器（擴展版）
處理紅包相關的所有功能
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from loguru import logger
from decimal import Decimal
from datetime import datetime, timedelta
import re

from shared.config.settings import get_settings
from shared.database.connection import get_db
from shared.database.models import User, RedPacket, RedPacketClaim, CurrencyType, RedPacketType, RedPacketStatus
from shared.database.connection import get_db
from bot.keyboards import get_packets_menu, get_back_to_main
from bot.constants import PacketConstants
from bot.utils.packet_helpers import extract_packet_data, format_packet_info, get_packet_type_text
from bot.utils.i18n import t, get_user_language

settings = get_settings()


async def packets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理紅包菜單回調（不處理 packets:send:* 開頭的回調，這些由 send_packet_menu_callback 處理）"""
    from bot.utils.user_helpers import get_user_from_update
    
    query = update.callback_query
    if not query:
        return
    
    # 如果是以 packets:send 開頭，不處理（由 send_packet_menu_callback 處理）
    if query.data and query.data.startswith("packets:send"):
        logger.debug(f"packets_callback ignoring packets:send callback: {query.data}")
        return
    
    await query.answer()
    
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    
    # 獲取用戶（帶緩存）
    db_user = await get_user_from_update(update, context)
    if not db_user:
        await query.message.reply_text("請先使用 /start 註冊")
        return
    
    if action == "list":
        await show_packets_list(query, db_user)
    elif action == "send":
        await show_send_packet_guide(query, db_user)
    elif action == "send_menu":
        # send_menu 應該由 send_packet_menu_callback 處理，但為了兼容性也處理
        await send_packet_menu_callback(update, context)
    elif action == "my":
        await show_my_packets(query, db_user)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理用戶文本輸入（金額、數量、群組 ID/鏈接或祝福語）"""
    from bot.utils.user_helpers import get_user_from_update
    from bot.keyboards.reply_keyboards import (
        get_send_packet_amount_keyboard,
        get_send_packet_count_keyboard,
        get_send_packet_group_keyboard,
        get_packets_reply_keyboard,
    )
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    
    text = update.message.text.strip()
    
    # 獲取用戶（帶緩存）
    db_user = await get_user_from_update(update, context)
    if not db_user:
        return
    
    # 檢查發紅包流程步驟
    step = context.user_data.get('send_packet_step')
    packet_data = context.user_data.get('send_packet', {})
    
    # 處理自定義金額輸入
    if step == 'amount_input':
        try:
            # 嘗試解析為數字（支持小數）
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text(t("amount_must_positive", user=db_user))
                return
            
            packet_data['amount'] = amount
            context.user_data['send_packet'] = packet_data
            context.user_data['send_packet_step'] = 'count'
            
            currency = packet_data.get('currency', 'usdt')
            packet_type = packet_data.get('packet_type', 'random')
            
            from bot.handlers.packets import show_count_input
            query = type('Query', (), {
                'edit_message_text': lambda self, *args, **kwargs: update.message.reply_text(*args, **kwargs),
                'message': update.message
            })()
            await show_count_input(query, db_user, context)
            await update.message.reply_text(
                t("select_count", user=db_user),
                reply_markup=get_send_packet_count_keyboard(currency, packet_type, str(amount)),
            )
            return
        except ValueError:
            await update.message.reply_text(t("invalid_amount", user=db_user))
            return
    
    # 處理自定義數量輸入
    elif step == 'count_input':
        try:
            count = int(text)
            if count <= 0:
                await update.message.reply_text("數量必須大於0，請重新輸入：")
                return
            if count > PacketConstants.MAX_COUNT:
                await update.message.reply_text(f"數量不能超過 {PacketConstants.MAX_COUNT}，請重新輸入：")
                return
            
            packet_data['count'] = count
            context.user_data['send_packet'] = packet_data
            context.user_data['send_packet_step'] = 'group'
            
            # 如果是紅包炸彈，需要設置炸彈數字
            if packet_data.get('packet_type') == 'equal':
                if count == 5:
                    packet_data['bomb_number'] = None  # 雙雷
                elif count == 10:
                    packet_data['bomb_number'] = None  # 單雷
                else:
                    await update.message.reply_text("紅包炸彈只能選擇 5 份（雙雷）或 10 份（單雷），請重新輸入：")
                    return
                context.user_data['send_packet'] = packet_data
            
            from bot.handlers.packets import show_group_selection
            query = type('Query', (), {
                'edit_message_text': lambda self, *args, **kwargs: update.message.reply_text(*args, **kwargs),
                'message': update.message
            })()
            await show_group_selection(query, db_user, context)
            await update.message.reply_text(
                "輸入群組 ID 或鏈接：",
                reply_markup=get_send_packet_group_keyboard(),
            )
            return
        except ValueError:
            await update.message.reply_text("請輸入有效的數字，例如：20")
            return
    
    # 處理群組 ID 輸入
    elif step == 'group_input' or context.user_data.get('waiting_for_group'):
        logger.info(f"Processing group input for user {db_user.tg_id}, text='{text}', step={step}, waiting_for_group={context.user_data.get('waiting_for_group')}")
        context.user_data['waiting_for_group'] = True
        context.user_data['send_packet_step'] = 'group_input'
        await handle_group_input(update, db_user, text, context)
        return
    
    # 處理祝福語輸入
    elif context.user_data.get('waiting_for_message'):
        await handle_message_input(update, db_user, text, context)
        return


async def handle_group_input(update, db_user, text, context):
    """處理群組 ID/鏈接輸入 - 支持只输入用户名（自动补全@和t.me/）"""
    from bot.utils.security import validate_chat_id
    import re
    
    packet_data = context.user_data.get('send_packet', {})
    
    # 清理输入
    text = text.strip()
    
    # 嘗試解析群組 ID 或鏈接
    chat_id = validate_chat_id(text)
    
    # 如果还不是有效的ID，尝试解析为群组用户名
    if chat_id is None:
        username = None
        
        # 方式1: 匹配 t.me/xxx 或 https://t.me/xxx
        match = re.search(r'(?:https?://)?(?:t\.me/|@)([a-zA-Z0-9_]+)', text, re.IGNORECASE)
        if match:
            username = match.group(1)
        # 方式2: 如果只是纯用户名（不包含@或t.me/），自动补全
        elif re.match(r'^[a-zA-Z0-9_]+$', text):
            # 只包含字母、数字、下划线，认为是用户名
            username = text
            logger.info(f"Auto-completing username: {username}")
        
        if username:
            try:
                from telegram import Bot
                bot = Bot(token=settings.BOT_TOKEN)
                # 尝试获取群组信息（自动添加@前缀）
                chat = await bot.get_chat(f"@{username}")
                chat_id = chat.id
                logger.info(f"Successfully got chat_id {chat_id} from username @{username}")
            except Exception as e:
                logger.error(f"Error getting chat from username @{username}: {e}", exc_info=True)
                await update.message.reply_text(
                    f"無法獲取群組信息：{str(e)}\n\n請確保：\n1. 群組用戶名正確（已自動補全 @{username}）\n2. Bot 在群組中\n3. 群組有公開 username\n\n也可以輸入：\n• 群組 ID（數字）\n• 完整鏈接：https://t.me/{username}",
                    parse_mode="Markdown"
                )
                return
    
    if chat_id:
        packet_data['chat_id'] = chat_id
        context.user_data['send_packet'] = packet_data
        context.user_data.pop('waiting_for_group', None)
        context.user_data['send_packet_step'] = 'confirm'
        
        # 顯示確認界面
        # 检查用户是通过内联按钮还是底部键盘进入的
        # 关键：如果是从底部键盘流程进入（通过handle_reply_keyboard），use_inline_buttons应该是False
        # 如果是从内联按钮流程进入（通过send_packet_menu_callback），use_inline_buttons应该是True
        currency = packet_data.get('currency', 'usdt')
        packet_type = packet_data.get('packet_type', 'random')
        amount = packet_data.get('amount', 0)
        count = packet_data.get('count', 1)
        message = packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
        bomb_number = packet_data.get('bomb_number')
        
        text = f"""
✅ *確認發送紅包*

*紅包信息：*
• 幣種：{currency.upper()}
• 類型：{"手氣最佳" if packet_type == "random" else "紅包炸彈"}
• 金額：{amount} {currency.upper()}
• 數量：{count} 份
• 祝福語：{message}
• 群組 ID：{chat_id}

請確認是否發送：
"""
        
        # 检查是否应该使用内联按钮
        # 关键修复：如果update有callback_query，说明是从内联按钮来的；否则是从底部键盘来的
        # 同时检查use_inline_buttons标志，但优先检查是否有callback_query
        has_callback_query = hasattr(update, 'callback_query') and update.callback_query is not None
        use_inline = context.user_data.get('use_inline_buttons', False) or has_callback_query
        
        logger.info(f"handle_group_input: use_inline={use_inline}, has_callback_query={has_callback_query}, use_inline_buttons_flag={context.user_data.get('use_inline_buttons', False)}")
        
        if use_inline:
            # 使用内联按钮（内联按钮流程）
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            # 生成callback_data，确保不超过64字节
            msg_flag = 'default' if message == PacketConstants.DEFAULT_MESSAGE else 'custom'
            bomb_num_str = str(bomb_number) if bomb_number is not None else ''
            confirm_callback = f"packets:send:confirm:{currency}:{packet_type}:{amount}:{count}:{bomb_num_str}:{msg_flag}:{chat_id}"
            
            # 如果超过64字节，使用简化格式
            if len(confirm_callback) > 64:
                confirm_callback = f"packets:send:confirm:{currency}:{packet_type}:{amount}:{count}:{chat_id}"
                # 存储完整数据到context
                if 'pending_confirm' not in context.user_data:
                    context.user_data['pending_confirm'] = {}
                context.user_data['pending_confirm'][str(chat_id)] = {
                    'bomb_number': bomb_number,
                    'message': message
                }
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ 確認發送", callback_data=confirm_callback),
                    InlineKeyboardButton("❌ 取消", callback_data="menu:packets"),
                ],
            ]
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # 使用底部键盘（底部键盘流程）
            # 关键：确保use_inline_buttons标志为False，这样后续的确认发送也会使用底部键盘
            context.user_data['use_inline_buttons'] = False
            from bot.keyboards.reply_keyboards import get_send_packet_confirm_keyboard
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_send_packet_confirm_keyboard(),
            )
    else:
        await update.message.reply_text(
            "無法識別群組 ID 或鏈接。\n\n請輸入：\n• 群組 ID（數字，例如：-1001234567890）\n• 群組鏈接（例如：https://t.me/groupname 或 @groupname）",
            parse_mode="Markdown"
        )


async def handle_message_input(update, db_user, text, context):
    """處理祝福語輸入"""
    from bot.utils.security import sanitize_message
    
    packet_data = context.user_data.get('send_packet', {})
    packet_data['message'] = sanitize_message(text)  # 使用安全清理
    context.user_data['send_packet'] = packet_data
    context.user_data.pop('waiting_for_message', None)
    
    # 進入群組選擇
    await show_group_selection_from_message(update, db_user, context)


async def show_group_selection_from_message(update, db_user, context):
    """從消息中顯示群組選擇"""
    packet_data = context.user_data.get('send_packet', {})
    
    # 在會話內獲取用戶發過紅包的群組，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内查询红包
        packets = db.query(RedPacket).filter(
            RedPacket.sender_id == user.id
        ).order_by(RedPacket.created_at.desc()).limit(10).all()
        
        text = f"""
➕ *發紅包 - 選擇群組*

*紅包信息：*
• 幣種：{packet_data.get('currency', 'usdt').upper()}
• 類型：{"手氣最佳" if packet_data.get('packet_type') == "random" else "紅包炸彈"}
• 金額：{packet_data.get('amount')} {packet_data.get('currency', 'usdt').upper()}
• 數量：{packet_data.get('count')} 份
• 祝福語：{packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)}

請選擇群組：
"""
        
        keyboard = []
        
        # 在会话内访问packet属性
        seen_chats = set()
        for packet in packets[:5]:
            if packet.chat_id and packet.chat_id not in seen_chats:
                seen_chats.add(packet.chat_id)
                chat_title = packet.chat_title or f"群組 {packet.chat_id}"
                keyboard.append([
                    InlineKeyboardButton(
                        f"📱 {chat_title[:20]}",
                        callback_data=f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{packet_data.get('bomb_number', '')}:{packet_data.get('message', 'default')}:{packet.chat_id}"
                    ),
                ])
        
        keyboard.append([
            InlineKeyboardButton("📝 輸入群組鏈接/ID", callback_data=f"packets:send:group_input:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{packet_data.get('bomb_number', '')}:{packet_data.get('message', 'default')}"),
        ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
        ])
        
        # 在会话内完成所有操作后再发送消息
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def confirm_and_send_from_message(update, db_user, context):
    """從消息確認並發送紅包"""
    packet_data = context.user_data.get('send_packet', {})
    
    currency = packet_data.get('currency', 'usdt')
    packet_type = packet_data.get('packet_type', 'random')
    amount = Decimal(str(packet_data.get('amount', 0)))
    count = int(packet_data.get('count', 1))
    bomb_number = packet_data.get('bomb_number')
    message = packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
    chat_id = packet_data.get('chat_id')
    
    if not chat_id:
        await update.message.reply_text("請選擇或輸入群組")
        return
    
    # 驗證參數
    if amount <= 0 or count <= 0:
        await update.message.reply_text("金額和數量必須大於0")
        return
    
    if count > PacketConstants.MAX_COUNT:
        await update.message.reply_text(f"每個紅包最多{PacketConstants.MAX_COUNT}份")
        return
    
    # ========================================
    # 检查机器人和发送者是否在群组中（必须通过才能创建红包）
    # ========================================
    bot_in_group = False
    sender_in_group = False
    
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        bot = Bot(token=settings.BOT_TOKEN)
        sender_tg_id = db_user.tg_id
        
        # 检查机器人是否在群组中
        try:
            # 先獲取機器人信息
            bot_info = await bot.get_me()
            bot_member = await bot.get_chat_member(chat_id, bot_info.id)
            bot_status = bot_member.status
            if bot_status in ['left', 'kicked']:
                # 机器人不在群组中
                await update.message.reply_text(
                    f"""❌ *機器人不在群組中*

機器人需要先加入群組才能發送紅包。

*解決方案：*
1. 在群組中添加機器人 @{settings.BOT_USERNAME or 'luckyred2025_bot'}
2. 確保機器人有發送消息的權限
3. 然後重新嘗試發送紅包

*群組 ID：* `{chat_id}`""",
                    parse_mode="Markdown"
                )
                return
            bot_in_group = True
            logger.info(f"Bot is in group {chat_id}, status: {bot_status}")
        except TelegramError as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg or "bot is not a member" in error_msg or "forbidden" in error_msg:
                await update.message.reply_text(
                    f"""❌ *機器人不在群組中*

機器人需要先加入群組才能發送紅包。

*解決方案：*
1. 確認群組 ID 正確：`{chat_id}`
2. 在群組中添加機器人 @{settings.BOT_USERNAME or 'luckyred2025_bot'}
3. 確保機器人有發送消息的權限

💡 *如何添加機器人到群組：*
• 打開群組設置 → 添加成員 → 搜索機器人""",
                    parse_mode="Markdown"
                )
                return
            else:
                # 其他錯誤也要阻止創建紅包
                logger.warning(f"Error checking bot membership: {e}")
                await update.message.reply_text(
                    f"""❌ *無法驗證機器人權限*

檢查機器人群組權限時出錯。

*請確保：*
1. 機器人已加入群組
2. 機器人有發送消息的權限

*群組 ID：* `{chat_id}`""",
                    parse_mode="Markdown"
                )
                return
        
        # 检查发送者是否在群组中（必须通过）
        try:
            sender_member = await bot.get_chat_member(chat_id, sender_tg_id)
            sender_status = sender_member.status
            if sender_status in ['left', 'kicked']:
                await update.message.reply_text(
                    f"""❌ *您不在目標群組中*

您需要先加入群組才能發送紅包到該群組。

*解決方案：*
1. 加入群組
2. 然後重新嘗試發送紅包

*群組 ID：* `{chat_id}`""",
                    parse_mode="Markdown"
                )
                return
            sender_in_group = True
            logger.info(f"Sender {sender_tg_id} is in group {chat_id}, status: {sender_status}")
        except TelegramError as e:
            # 发送者不在群组，阻止发送
            error_msg = str(e).lower()
            if "user not found" in error_msg or "forbidden" in error_msg:
                await update.message.reply_text(
                    f"""❌ *您不在目標群組中*

您需要先加入群組才能發送紅包。

*解決方案：*
1. 加入群組 `{chat_id}`
2. 然後重新嘗試發送紅包""",
                    parse_mode="Markdown"
                )
                return
            logger.warning(f"Could not verify sender membership: {e}")
            sender_in_group = True  # 無法驗證時允許繼續
    except Exception as e:
        logger.error(f"Error checking group membership: {e}", exc_info=True)
        await update.message.reply_text(
            f"""❌ *檢查群組權限失敗*

無法驗證群組成員資格，請稍後再試。

*錯誤：* {str(e)[:100]}""",
            parse_mode="Markdown"
        )
        return
    
    # 最終檢查
    if not bot_in_group:
        await update.message.reply_text(
            f"""❌ *機器人不在群組中*

請先將機器人添加到群組 `{chat_id}`""",
            parse_mode="Markdown"
        )
        return
    
    # 在會話內檢查餘額
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        balance = getattr(user, f"balance_{currency}", 0) or Decimal(0)
    if balance < amount:
        await update.message.reply_text(f"餘額不足，當前餘額: {float(balance):.2f}")
        return
    
    # 創建紅包
    try:
        from bot.utils.api_client import get_api_client
        from bot.utils.security import sanitize_message
        
        # 清理消息
        message = sanitize_message(message)
        
        # 使用統一的 API 客戶端
        api_client = get_api_client()
        
        # 在会话外使用db_user.tg_id（基本属性，不会触发会话问题）
        sender_tg_id = db_user.tg_id
        
        # 获取chat_title（如果是群组，尝试获取群组名称）
        chat_title = None
        try:
            from telegram import Bot
            bot = Bot(token=settings.BOT_TOKEN)
            chat = await bot.get_chat(chat_id)
            chat_title = chat.title if hasattr(chat, 'title') else None
        except Exception as e:
            logger.debug(f"Could not get chat title for {chat_id}: {e}")
            # 如果无法获取，使用chat_id作为标题
            chat_title = f"群組 {chat_id}" if chat_id < 0 else None
        
        result = await api_client.post(
            "/redpackets/create",
            data={
                "currency": currency,
                "packet_type": packet_type,
                "total_amount": float(amount),
                "total_count": count,
                "message": message,
                "chat_id": chat_id,
                "chat_title": chat_title,
                "bomb_number": bomb_number,
            },
            tg_id=sender_tg_id
        )
        
        # 記錄紅包操作
        from bot.utils.logging_helpers import log_packet_action
        log_packet_action(
            user_id=sender_tg_id,
            action="create",
            packet_id=result.get('id'),
            amount=float(amount),
            currency=currency,
            success=True
        )
        
        # 清除用戶緩存（因為餘額已更新）
        from bot.utils.cache import UserCache
        UserCache.invalidate(sender_tg_id)
        
        # ✅ 發送紅包消息到群組
        packet_uuid = result.get('uuid', '')
        try:
            from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
            bot = Bot(token=settings.BOT_TOKEN)
            
            # 構建群組中的紅包消息
            type_text = "🎲 手氣最佳" if packet_type == "random" else "💣 紅包炸彈"
            group_message = f"""
🧧 *{message}*

{type_text}
💰 金額：{float(amount):.2f} {currency.upper()}
👥 數量：{count} 份

🎁 點擊下方按鈕搶紅包！
"""
            # 構建搶紅包按鈕
            claim_keyboard = [[
                InlineKeyboardButton(
                    "🧧 搶紅包",
                    url=f"{settings.MINIAPP_URL}/claim/{packet_uuid}"
                )
            ]]
            
            await bot.send_message(
                chat_id=chat_id,
                text=group_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(claim_keyboard)
            )
            logger.info(f"Red packet message sent to group {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send red packet message to group {chat_id}: {e}")
            # 群組發送失敗不影響紅包創建成功
        
        # 检查是否应该使用内联按钮（根据use_inline_buttons标志）
        use_inline = context.user_data.get('use_inline_buttons', False)
        
        if use_inline:
            # 使用内联按钮返回
            keyboard = [
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
            await update.message.reply_text(
                f"✅ *紅包發送成功！*\n\n"
                f"*紅包信息：*\n"
                f"• UUID: `{packet_uuid}`\n"
                f"• 金額：{float(amount):.2f} {currency.upper()}\n"
                f"• 數量：{count} 份\n"
                f"• 祝福語：{message}\n\n"
                f"紅包已發送到群組！",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # 使用底部键盘返回
            from bot.keyboards.reply_keyboards import get_packets_reply_keyboard
            await update.message.reply_text(
                f"✅ *紅包發送成功！*\n\n"
                f"*紅包信息：*\n"
                f"• UUID: `{packet_uuid}`\n"
                f"• 金額：{float(amount):.2f} {currency.upper()}\n"
                f"• 數量：{count} 份\n"
                f"• 祝福語：{message}\n\n"
                f"紅包已發送到群組！",
                parse_mode="Markdown",
                reply_markup=get_packets_reply_keyboard(),
            )
        
        # 清理状态
        context.user_data.pop('send_packet', None)
        context.user_data.pop('send_packet_step', None)
        context.user_data.pop('use_inline_buttons', None)
    except Exception as e:
        logger.error(f"Error sending packet: {e}", exc_info=True)
        error_msg = str(e)
        
        # 更详细的错误处理
        if "餘額不足" in error_msg or "Insufficient balance" in error_msg:
            error_msg = "餘額不足"
        elif "connection" in error_msg.lower() or "Connection" in error_msg or "All connection attempts failed" in error_msg:
            # API 连接失败
            from shared.config.settings import get_settings
            api_settings = get_settings()
            error_msg = f"""無法連接到 API 服務器

請檢查：
• API 服務器是否運行中
• API URL: `{api_settings.API_BASE_URL}`
• 網絡連接是否正常

💡 解決方案：
1. 打開新的命令提示符窗口
2. 運行: `.\啟動API服務器.bat`
3. 或手動啟動: `cd api && python main.py`
4. 等待看到 "Uvicorn running on http://0.0.0.0:8080"
5. 然後重新嘗試發送紅包"""
        elif "HTTP" in error_msg or "Request" in error_msg:
            error_msg = "網絡錯誤，請稍後再試"
        elif "timeout" in error_msg.lower():
            error_msg = "請求超時，請稍後再試"
        
        # 检查是否应该使用内联按钮（根据use_inline_buttons标志）
        use_inline = context.user_data.get('use_inline_buttons', False)
        
        if use_inline:
            # 使用内联按钮返回
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
            await update.message.reply_text(
                f"❌ *發送失敗*\n\n{error_msg}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # 使用底部键盘返回
            from bot.keyboards.reply_keyboards import get_packets_reply_keyboard
            await update.message.reply_text(
                f"❌ *發送失敗*\n\n{error_msg}",
                parse_mode="Markdown",
                reply_markup=get_packets_reply_keyboard(),
            )
    
    # 清除臨時數據
    context.user_data.pop('send_packet', None)
    context.user_data.pop('waiting_for_group', None)
    context.user_data.pop('waiting_for_message', None)
    context.user_data.pop('send_packet_step', None)
    context.user_data.pop('use_inline_buttons', None)


async def show_packets_list(query, db_user):
    """顯示可搶的紅包列表"""
    # 在會話內完成所有操作
    with get_db() as db:
        # 獲取未過期且未領完的紅包
        packets = db.query(RedPacket).filter(
            RedPacket.status == RedPacketStatus.ACTIVE,
            RedPacket.expires_at > datetime.utcnow()
        ).order_by(RedPacket.created_at.desc()).limit(10).all()
        
        # 在会话内访问packet属性
        if not packets:
            text = """
📋 *可搶紅包*

目前沒有可搶的紅包

💡 提示：在群組中發送紅包，其他用戶就可以搶了
"""
            keyboard = [
                [
                    InlineKeyboardButton("➕ 發紅包", callback_data="packets:send"),
                ],
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
        else:
            text = "📋 *可搶紅包列表*\n\n"
            for i, packet in enumerate(packets[:5], 1):
                claimed = packet.claimed_count or 0
                remaining = packet.total_count - claimed
                text += f"{i}. {packet.message or PacketConstants.DEFAULT_MESSAGE}\n"
                text += f"   💰 {float(packet.total_amount):.2f} {packet.currency.value.upper()}\n"
                text += f"   👥 {remaining}/{packet.total_count} 份剩餘\n\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("📱 查看完整列表", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/packets")),
                ],
                [
                    InlineKeyboardButton("➕ 發紅包", callback_data="packets:send"),
                ],
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
        
        # 在会话内完成所有操作后再发送消息
        # 检查消息是否需要更新，避免"Message is not modified"错误
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                await query.answer("已顯示", show_alert=False)
                logger.debug(f"Message not modified in show_amount_input, user {db_user.tg_id}")
            else:
                logger.error(f"Error editing message in show_amount_input: {e}", exc_info=True)
                raise


async def show_send_packet_guide(query, db_user):
    """顯示發紅包選項"""
    # 在会话内重新查询用户以确保数据最新
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await query.edit_message_text(t("error", user=db_user))
            return
        
        text = f"""
➕ *{t('send_packet_title', user=user)}*

{t('select_operation', user=user)}

*方式一：* 在群組中使用命令
在群組中輸入：`/send <金額> <數量> [祝福語]`

*方式二：* 使用機器人菜單
選擇群組和設置參數
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📝 使用菜單發送", callback_data="packets:send_menu"),
            ],
            [
                InlineKeyboardButton(t("return_main", user=user), callback_data="menu:packets"),
            ],
        ]
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def send_packet_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理發紅包菜單回調"""
    # ⚠️ 关键修复：在函数最开始就引用 User，确保 Python 知道它是外部作用域的变量
    # 这必须在任何 try/except 之前，否则 Python 可能将其视为局部变量
    # 使用多种方式确保 Python 知道 User 是外部作用域的变量
    _user_ref = User  # 显式引用，告诉 Python User 是从外部作用域来的
    _ = User.__name__  # 访问属性，进一步确保 Python 知道它是外部作用域的
    
    query = update.callback_query
    if not query:
        logger.error("send_packet_menu_callback called but no callback_query")
        return
    
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[SEND_PACKET] Received callback: '{query.data}' from user {user_id}")
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"[SEND_PACKET] Error answering query: {e}")
    
    user = update.effective_user
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    sub_action = parts[2] if len(parts) > 2 else ""
    
    logger.info(f"[SEND_PACKET] Parsed: action={action}, sub_action={sub_action}, parts={parts}")
    
    # 獲取用戶（在會話內重新查詢，避免會話分離錯誤）
    # 注意：User 已经在文件顶部导入，这里不再重复导入
    from shared.database.connection import get_db
    
    # 初始化db_user为None，确保在except块中可用
    db_user = None
    
    # 在会话内完成所有操作
    # 注意：User 在文件顶部已导入，这里直接使用，Python会从外部作用域获取
    with get_db() as db:
        db_user = db.query(User).filter(User.tg_id == user_id).first()
        if not db_user:
            logger.error(f"[SEND_PACKET] User {user_id} not found")
            await query.message.reply_text("請先使用 /start 註冊")
            return
        
        # 在会话内访问所有需要的属性，确保数据已加载
        _ = db_user.id
        _ = db_user.tg_id
        _ = db_user.balance_usdt
        _ = db_user.balance_ton
        _ = db_user.balance_points
    
    # 注意：User 已经在函数开始处引用（第598行），这里不需要再次引用
    # 直接使用 User 即可，Python 已经知道它是外部作用域的变量
    
    try:
        if action == "send_menu":
            logger.info(f"[SEND_PACKET] Showing send packet menu for user {user_id}")
            # 重新在会话内查询以确保数据最新
            with get_db() as db:
                db_user = db.query(User).filter(User.tg_id == user_id).first()
                if db_user:
                    await show_send_packet_menu(query, db_user)
        elif action == "send":
            # 重新在会话内查询以确保数据最新
            with get_db() as db:
                db_user = db.query(User).filter(User.tg_id == user_id).first()
                if not db_user:
                    await query.message.reply_text("請先使用 /start 註冊")
                    return
                
                # 标记用户使用的是内联按钮流程
                context.user_data['use_inline_buttons'] = True
                
                # ✅ 只在第一次進入時移除底部鍵盤（不發送消息，避免重複）
                if not sub_action:
                    from telegram import ReplyKeyboardRemove
                    try:
                        await query.message.reply_text(
                            "使用內聯按鈕進行操作 👇",
                            reply_markup=ReplyKeyboardRemove()
                        )
                    except Exception:
                        pass
                
                # 如果 sub_action 为空，显示发红包引导界面
                if not sub_action:
                    logger.info(f"[SEND_PACKET] Showing send packet guide for user {user_id}")
                    await show_send_packet_guide(query, db_user)
                elif sub_action == "type":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    logger.info(f"[SEND_PACKET] Showing packet type selection for user {user_id}, currency={currency}")
                    await show_packet_type_selection(query, db_user, currency, context)
                    logger.info(f"[SEND_PACKET] Successfully showed packet type selection for user {user_id}")
                elif sub_action == "amount":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    await show_amount_input(query, db_user, currency, packet_type)
                elif sub_action == "count":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    amount = parts[5] if len(parts) > 5 else None
                    # 检查是否已经选择了数量（parts[6]）
                    count = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else None
                    
                    if count is not None:
                        # 用户已经选择了数量，直接进入下一步
                        context.user_data['send_packet'] = {
                            'currency': currency,
                            'packet_type': packet_type,
                            'amount': amount,
                            'count': count,
                        }
                        # 如果是红包炸弹，需要选择炸弹数字
                        if packet_type == "equal":
                            await show_bomb_number_selection(query, db_user, context)
                        else:
                            # 普通红包，进入祝福语输入
                            await show_message_input(query, db_user, context)
                    else:
                        # 还没有选择数量，显示数量选择界面
                        context.user_data['send_packet'] = {
                            'currency': currency,
                            'packet_type': packet_type,
                            'amount': amount,
                        }
                        await show_count_input(query, db_user, context)
                elif sub_action == "bomb":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    amount = parts[5] if len(parts) > 5 else None
                    count = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else None
                    context.user_data['send_packet'] = {
                        'currency': currency,
                        'packet_type': packet_type,
                        'amount': amount,
                        'count': count,
                    }
                    await show_bomb_number_selection(query, db_user, context)
                elif sub_action == "message":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    amount = parts[5] if len(parts) > 5 else None
                    count = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else None
                    bomb_number = int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else None
                    context.user_data['send_packet'] = {
                        'currency': currency,
                        'packet_type': packet_type,
                        'amount': amount,
                        'count': count,
                        'bomb_number': bomb_number,
                    }
                    await show_message_input(query, db_user, context)
                elif sub_action == "group":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    amount = parts[5] if len(parts) > 5 else None
                    # 处理count，可能是空字符串
                    count = None
                    if len(parts) > 6 and parts[6]:
                        try:
                            count = int(parts[6])
                        except (ValueError, TypeError):
                            count = None
                    # 处理bomb_number，可能是空字符串
                    bomb_number = None
                    if len(parts) > 7 and parts[7]:
                        try:
                            bomb_number = int(parts[7])
                        except (ValueError, TypeError):
                            bomb_number = None
                    # 处理message，如果parts[8]是"default"或空，使用默认消息
                    message = PacketConstants.DEFAULT_MESSAGE
                    if len(parts) > 8:
                        if parts[8] and parts[8] != "default":
                            # 如果parts[8]不是"default"，可能是自定义消息（但通常不会在这里，因为callback_data限制）
                            message = parts[8]
                        # 如果parts[8]是"default"或空字符串，使用默认消息（已经在上面设置了）
                    
                    context.user_data['send_packet'] = {
                        'currency': currency,
                        'packet_type': packet_type,
                        'amount': amount,
                        'count': count,
                        'bomb_number': bomb_number,
                        'message': message,
                    }
                    await show_group_selection(query, db_user, context)
                elif sub_action == "group_input":
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    amount = parts[5] if len(parts) > 5 else None
                    # 处理count，可能是空字符串
                    count = None
                    if len(parts) > 6 and parts[6]:
                        try:
                            count = int(parts[6])
                        except (ValueError, TypeError):
                            count = None
                    # 处理bomb_number，可能是空字符串
                    bomb_number = None
                    if len(parts) > 7 and parts[7]:
                        try:
                            bomb_number = int(parts[7])
                        except (ValueError, TypeError):
                            bomb_number = None
                    # 处理message，如果parts[8]是"default"或空，使用默认消息
                    message = PacketConstants.DEFAULT_MESSAGE
                    if len(parts) > 8:
                        if parts[8] and parts[8] != "default":
                            message = parts[8]
                    
                    context.user_data['send_packet'] = {
                        'currency': currency,
                        'packet_type': packet_type,
                        'amount': amount,
                        'count': count,
                        'bomb_number': bomb_number,
                        'message': message,
                    }
                    # 设置状态，确保后续文本输入能被识别
                    context.user_data['send_packet_step'] = 'group_input'
                    context.user_data['waiting_for_group'] = True
                    # 标记用户使用的是内联按钮流程
                    context.user_data['use_inline_buttons'] = True
                    logger.info(f"Setting waiting_for_group=True for user {db_user.tg_id}, step=group_input, use_inline_buttons=True")
                    await show_group_link_input(query, db_user, context)
                elif sub_action == "confirm":
                    # 解析callback_data参数
                    chat_id = None
                    if len(parts) > 9:
                        try:
                            chat_id = int(parts[9])
                        except (ValueError, TypeError):
                            pass
                    
                    # 如果callback_data被简化了，从context中恢复message和bomb_number
                    if 'pending_confirm' in context.user_data and chat_id and str(chat_id) in context.user_data['pending_confirm']:
                        pending = context.user_data['pending_confirm'][str(chat_id)]
                        context.user_data.setdefault('send_packet', {})['bomb_number'] = pending.get('bomb_number')
                        context.user_data.setdefault('send_packet', {})['message'] = pending.get('message', PacketConstants.DEFAULT_MESSAGE)
                        # 清理临时数据
                        del context.user_data['pending_confirm'][str(chat_id)]
                    else:
                        # 从callback_data中解析message（如果存在）
                        if len(parts) > 8:
                            msg_flag = parts[8]
                            if msg_flag == 'default':
                                context.user_data.setdefault('send_packet', {})['message'] = PacketConstants.DEFAULT_MESSAGE
                            # 如果msg_flag是'custom'，message应该已经在context中
                    
                    if chat_id:
                        context.user_data.setdefault('send_packet', {})['chat_id'] = chat_id
                    
                    # 直接使用外层已获取的 db_user（已在会话内）
                    # 注意：db_user 已经在外层 with get_db() 块中查询获得
                    await confirm_and_send_packet(query, db_user, context)
                elif sub_action == "amount_custom":
                    # 處理自定義金額輸入
                    currency = parts[3] if len(parts) > 3 else "usdt"
                    packet_type = parts[4] if len(parts) > 4 else "random"
                    context.user_data['send_packet'] = {
                        'currency': currency,
                        'packet_type': packet_type,
                    }
                    context.user_data['send_packet_step'] = 'amount_input'
                    
                    # 重新在会话内查询用户
                    with get_db() as db:
                        db_user = db.query(User).filter(User.tg_id == user_id).first()
                        if db_user:
                            await query.edit_message_text(
                                t("enter_amount", user=db_user),
                                parse_mode="Markdown"
                            )
                            await query.message.reply_text(
                                t("enter_amount", user=db_user),
                                reply_markup=ReplyKeyboardMarkup([[
                                    KeyboardButton(t("cancel", user=db_user))
                                ]], resize_keyboard=True),
                            )
    except Exception as e:
        logger.error(f"[SEND_PACKET] Error processing callback: {e}", exc_info=True)
        try:
            # 簡化錯誤處理，直接發送錯誤消息
            await query.message.reply_text("發生錯誤，請稍後再試")
        except Exception as e2:
            logger.error(f"Error in error handler: {e2}", exc_info=True)


async def show_send_packet_menu(query, db_user, use_inline_buttons: bool = True):
    """顯示發紅包主菜單
    
    Args:
        query: 查詢對象
        db_user: 用戶對象
        use_inline_buttons: 是否使用內聯按鈕模式（True=內聯按鈕，False=底部鍵盤）
    """
    # 在會話內重新查詢用戶以確保數據最新，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            # 如果查询失败，使用传入的db_user（可能已脱离会话，但至少可以显示错误）
            try:
                await query.edit_message_text(t("error", user=db_user))
            except:
                # 如果edit失败，尝试reply_text
                if hasattr(query, 'message') and query.message:
                    await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内访问所有需要的属性
        usdt_balance = float(user.balance_usdt or 0)
        ton_balance = float(user.balance_ton or 0)
        points_balance = user.balance_points or 0
        
        # 在会话内获取翻译文本（t函数可能会访问user属性）
        send_packet_title = t('send_packet_title', user=user)
        current_balance = t('current_balance', user=user)
        select_currency = t('select_currency', user=user)
        return_main = t("return_main", user=user)
        
        text = f"""
➕ *{send_packet_title}*

*{current_balance}*
• USDT: `{usdt_balance:.4f}`
• TON: `{ton_balance:.4f}`
• 能量: `{points_balance}`

{select_currency}
"""
        
        if use_inline_buttons:
            # 內聯按鈕模式
            keyboard = [
                [
                    InlineKeyboardButton("USDT", callback_data="packets:send:type:usdt"),
                    InlineKeyboardButton("TON", callback_data="packets:send:type:ton"),
                ],
                [
                    InlineKeyboardButton("能量", callback_data="packets:send:type:points"),
                ],
                [
                    InlineKeyboardButton(return_main, callback_data="menu:packets"),
                ],
            ]
            
            # 在会话内完成所有操作后再发送消息
            # 检查消息是否需要更新，避免"Message is not modified"错误
            try:
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except Exception as e:
                error_msg = str(e)
                if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                    await query.answer("已顯示", show_alert=False)
                    logger.debug(f"Message not modified in show_send_packet_menu, user {db_user.tg_id}")
                else:
                    logger.error(f"Error editing message in show_send_packet_menu: {e}", exc_info=True)
                    raise
        else:
            # 底部鍵盤模式 - 只顯示消息，不帶內聯按鈕
            try:
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                )
            except Exception as e:
                error_msg = str(e)
                if "Message is not modified" not in error_msg.lower():
                    logger.error(f"Error editing message in show_send_packet_menu (reply mode): {e}", exc_info=True)


async def show_packet_type_selection(query, db_user, currency: str, context=None):
    """顯示紅包類型選擇
    
    Args:
        query: 查詢對象
        db_user: 用戶對象
        currency: 幣種
        context: 上下文（用於檢查 use_inline_buttons 標誌）
    """
    logger.info(f"[SHOW_TYPE] Showing packet type selection for currency={currency}, user={db_user.tg_id}")
    
    # 檢查是否使用內聯按鈕
    use_inline = True
    if context and hasattr(context, 'user_data'):
        use_inline = context.user_data.get('use_inline_buttons', True)
    
    try:
        # 在會話內重新查詢用戶以確保數據最新，並在會話內完成所有操作
        # 注意：User 已在文件頂部導入，不再重複導入
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            if not user:
                logger.error(f"[SHOW_TYPE] User {db_user.tg_id} not found in database")
                try:
                    await query.edit_message_text(t("error", user=db_user))
                except:
                    if hasattr(query, 'message') and query.message:
                        await query.message.reply_text("發生錯誤，請稍後再試")
                return
            
            # 在会话内访问所有需要的属性
            balance = float(getattr(user, f"balance_{currency}", 0) or 0)
            logger.info(f"[SHOW_TYPE] User {db_user.tg_id} balance for {currency}: {balance}")
            
            currency_upper = currency.upper()
            
            # 在会话内获取所有翻译文本
            send_packet_title = t('send_packet_title', user=user)
            current_balance = t('current_balance', user=user)
            select_type = t('select_type', user=user)
            random_amount = t('random_amount', user=user)
            fixed_amount = t('fixed_amount', user=user)
            return_main = t("return_main", user=user)
            
            # 檢查餘額，如果為 0 則提醒，但仍然允許繼續（用戶可能想先設置好紅包參數）
            balance_warning = ""
            if balance <= 0:
                currency_name = "USDT" if currency == "usdt" else "TON" if currency == "ton" else "能量"
                balance_warning = t("balance_warning", user=user, currency=currency_name, balance=balance)
            
            text = f"""
➕ *{send_packet_title} - {currency_upper}*

*{current_balance}* `{balance:.4f}` {currency_upper}{balance_warning}

*{select_type}*
• 🎲 {random_amount} - 隨機金額分配，領取完成後金額最大的用戶將被標記為"最佳手氣"
• 💣 {fixed_amount} - 固定金額分配，如果領取金額的小數點後最後一位數字與炸彈數字相同，將觸發炸彈

{select_type}：
"""
            
            if use_inline:
                # 內聯按鈕模式
                keyboard = [
                    [
                        InlineKeyboardButton(f"🎲 {random_amount}", callback_data=f"packets:send:amount:{currency}:random"),
                    ],
                    [
                        InlineKeyboardButton(f"💣 {fixed_amount}", callback_data=f"packets:send:amount:{currency}:equal"),
                    ],
                    [
                        InlineKeyboardButton(return_main, callback_data="packets:send_menu"),
                    ],
                ]
                
                # 在会话内完成所有操作后再发送消息
                logger.info(f"[SHOW_TYPE] Editing message for user {db_user.tg_id}")
                try:
                    await query.edit_message_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    logger.info(f"[SHOW_TYPE] Successfully showed packet type selection for user {db_user.tg_id}")
                except Exception as e:
                    error_msg = str(e)
                    if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                        await query.answer("已顯示", show_alert=False)
                        logger.debug(f"Message not modified in show_packet_type_selection, user {db_user.tg_id}")
                    else:
                        raise
            else:
                # 底部鍵盤模式 - 只編輯消息文本，不帶內聯按鈕
                try:
                    await query.edit_message_text(
                        text,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    error_msg = str(e)
                    if "Message is not modified" not in error_msg.lower():
                        logger.debug(f"Error editing message in show_packet_type_selection (reply mode): {e}")
    except Exception as e:
        logger.error(f"[SHOW_TYPE] Error showing packet type selection: {e}", exc_info=True)
        try:
            await query.message.reply_text(t("error", user=db_user))
        except:
            pass


async def show_amount_input(query, db_user, currency: str, packet_type: str):
    """顯示金額輸入"""
    # 在會話內重新查詢用戶以確保數據最新，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            try:
                await query.edit_message_text(t("error", user=db_user))
            except:
                if hasattr(query, 'message') and query.message:
                    await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内访问所有需要的属性
        balance = float(getattr(user, f"balance_{currency}", 0) or 0)
        
        currency_upper = currency.upper()
        
        # 在会话内获取所有翻译文本
        send_packet_title = t('send_packet_title', user=user)
        current_balance = t('current_balance', user=user)
        select_amount = t('select_amount', user=user)
        custom_amount = t("custom_amount", user=user)
        return_main = t("return_main", user=user)
        type_text = t("random_amount", user=user) if packet_type == "random" else t("fixed_amount", user=user)
        
        text = f"""
➕ *{send_packet_title} - {currency_upper} - {type_text}*

*{current_balance}* `{balance:.4f}` {currency_upper}

{select_amount}
"""
        
        # 根據餘額提供快捷金額選項
        quick_amounts = []
        if balance >= 100:
            quick_amounts = [10, 50, 100]
        elif balance >= 50:
            quick_amounts = [10, 20, 50]
        elif balance >= 10:
            quick_amounts = [5, 10, 20]
        else:
            quick_amounts = [1, 5, 10] if balance >= 1 else []
        
        keyboard = []
        if quick_amounts:
            row = []
            for amt in quick_amounts:
                if amt <= balance:
                    row.append(InlineKeyboardButton(str(amt), callback_data=f"packets:send:count:{currency}:{packet_type}:{amt}"))
            if row:
                keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton(custom_amount, callback_data=f"packets:send:amount_custom:{currency}:{packet_type}"),
        ])
        keyboard.append([
            InlineKeyboardButton(return_main, callback_data=f"packets:send:type:{currency}"),
        ])
        
        # 在会话内完成所有操作后再发送消息
        # 检查消息是否需要更新，避免"Message is not modified"错误
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                await query.answer("已顯示", show_alert=False)
                logger.debug(f"Message not modified in show_amount_input, user {db_user.tg_id}")
            else:
                logger.error(f"Error editing message in show_amount_input: {e}", exc_info=True)
                raise


async def show_count_input(query, db_user, context):
    """顯示數量輸入"""
    packet_data = context.user_data.get('send_packet', {})
    currency = packet_data.get('currency', 'usdt')
    packet_type = packet_data.get('packet_type', 'random')
    amount = packet_data.get('amount')
    
    if not amount:
        await query.answer("請先輸入金額", show_alert=True)
        return
    
    currency_upper = currency.upper()
    type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
    
    # 紅包炸彈只能選擇 5 或 10
    if packet_type == "equal":
        text = f"""
➕ *發紅包 - {currency_upper} - {type_text}*

*金額：* `{amount}` {currency_upper}

請選擇紅包數量：
💣 紅包炸彈只能選擇 5 份（雙雷）或 10 份（單雷）
"""
        keyboard = [
            [
                InlineKeyboardButton("5 份（雙雷）", callback_data=f"packets:send:bomb:{currency}:{packet_type}:{amount}:5"),
                InlineKeyboardButton("10 份（單雷）", callback_data=f"packets:send:bomb:{currency}:{packet_type}:{amount}:10"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data=f"packets:send:amount:{currency}:{packet_type}"),
            ],
        ]
    else:
        text = f"""
➕ *發紅包 - {currency_upper} - {type_text}*

*金額：* `{amount}` {currency_upper}

請選擇紅包數量（1-100）：
"""
        keyboard = [
            [
                InlineKeyboardButton("5", callback_data=f"packets:send:count:{currency}:{packet_type}:{amount}:5"),
                InlineKeyboardButton("10", callback_data=f"packets:send:count:{currency}:{packet_type}:{amount}:10"),
                InlineKeyboardButton("20", callback_data=f"packets:send:count:{currency}:{packet_type}:{amount}:20"),
            ],
            [
                InlineKeyboardButton("📝 自定義數量", callback_data=f"packets:send:count_custom:{currency}:{packet_type}:{amount}"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data=f"packets:send:amount:{currency}:{packet_type}"),
            ],
        ]
    
    # 检查消息是否需要更新，避免"Message is not modified"错误
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        error_msg = str(e)
        if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
            # 消息内容相同，只需要响应点击即可
            await query.answer("已選擇", show_alert=False)
            logger.debug(f"Message not modified for count input, user {db_user.tg_id}")
        else:
            # 其他错误，重新抛出
            logger.error(f"Error editing message in show_count_input: {e}", exc_info=True)
            raise


async def show_bomb_number_selection(query, db_user, context):
    """顯示炸彈數字選擇"""
    packet_data = context.user_data.get('send_packet', {})
    currency = packet_data.get('currency', 'usdt')
    packet_type = packet_data.get('packet_type', 'random')
    amount = packet_data.get('amount')
    count = packet_data.get('count')
    
    if packet_type != "equal":
        # 如果不是紅包炸彈，跳過這一步
        await show_message_input(query, db_user, context)
        return
    
    currency_upper = currency.upper()
    thunder_type = "單雷" if count == 10 else "雙雷"
    
    text = f"""
➕ *發紅包 - {currency_upper} - 紅包炸彈*

*金額：* `{amount}` {currency_upper}
*數量：* `{count}` 份（{thunder_type}）

請選擇炸彈數字（0-9）：
如果領取金額的小數點後最後一位數字與炸彈數字相同，將觸發炸彈
"""
    
    keyboard = []
    row = []
    for i in range(10):
        row.append(InlineKeyboardButton(str(i), callback_data=f"packets:send:message:{currency}:{packet_type}:{amount}:{count}:{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("◀️ 返回", callback_data=f"packets:send:count:{currency}:{packet_type}:{amount}"),
    ])
    
    # 检查消息是否需要更新，避免"Message is not modified"错误
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        error_msg = str(e)
        if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
            await query.answer("已顯示", show_alert=False)
            logger.debug(f"Message not modified for bomb number selection, user {db_user.tg_id}")
        else:
            logger.error(f"Error editing message in show_bomb_number_selection: {e}", exc_info=True)
            raise


async def show_message_input(query, db_user, context):
    """顯示祝福語輸入"""
    packet_data = context.user_data.get('send_packet', {})
    currency = packet_data.get('currency', 'usdt')
    packet_type = packet_data.get('packet_type', 'random')
    amount = packet_data.get('amount')
    count = packet_data.get('count')
    bomb_number = packet_data.get('bomb_number')
    
    currency_upper = currency.upper()
    type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
    
    text = f"""
➕ *發紅包 - {currency_upper} - {type_text}*

*金額：* `{amount}` {currency_upper}
*數量：* `{count}` 份
{f"*炸彈數字：* `{bomb_number}`" if bomb_number is not None else ""}

請輸入祝福語（可選）：
直接發送消息作為祝福語，或點擊使用默認祝福語
"""
    
    keyboard = [
        [
            InlineKeyboardButton("✅ 使用默認祝福語", callback_data=f"packets:send:group:{currency}:{packet_type}:{amount}:{count}:{bomb_number or ''}:default"),
        ],
        [
            InlineKeyboardButton("📝 輸入祝福語", callback_data=f"packets:send:message_input:{currency}:{packet_type}:{amount}:{count}:{bomb_number or ''}"),
        ],
        [
            InlineKeyboardButton("◀️ 返回", callback_data=f"packets:send:bomb:{currency}:{packet_type}:{amount}:{count}" if bomb_number is not None else f"packets:send:count:{currency}:{packet_type}:{amount}"),
        ],
    ]
    
    # 检查消息是否需要更新，避免"Message is not modified"错误
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        error_msg = str(e)
        if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
            await query.answer("已顯示", show_alert=False)
            logger.debug(f"Message not modified for message input, user {db_user.tg_id}")
        else:
            logger.error(f"Error editing message in show_message_input: {e}", exc_info=True)
            raise
    
    # 如果點擊了輸入祝福語，設置等待狀態
    if query.data and "message_input" in query.data:
        context.user_data['waiting_for_message'] = True


async def show_group_search(query, db_user, context):
    """顯示群組搜索結果（用於回覆鍵盤流程）"""
    packet_data = context.user_data.get('send_packet', {})
    
    # 在會話內獲取用戶發過紅包的群組，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            try:
                await query.edit_message_text("發生錯誤，請稍後再試")
            except:
                if hasattr(query, 'message') and query.message:
                    await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内查询红包
        packets = db.query(RedPacket).filter(
            RedPacket.sender_id == user.id
        ).order_by(RedPacket.created_at.desc()).limit(10).all()
        
        text = f"""
🔍 *查找群組*

*紅包信息：*
• 幣種：{packet_data.get('currency', 'usdt').upper()}
• 類型：{"手氣最佳" if packet_data.get('packet_type') == "random" else "紅包炸彈"}
• 金額：{packet_data.get('amount')} {packet_data.get('currency', 'usdt').upper()}
• 數量：{packet_data.get('count')} 份

*已發過紅包的群組：*
"""
        
        # 在会话内访问packet属性
        if not packets:
            text += "\n暫無已發過紅包的群組，請輸入群組 ID 或鏈接。"
        else:
            seen_chats = set()
            for i, packet in enumerate(packets[:5], 1):
                if packet.chat_id and packet.chat_id not in seen_chats:
                    seen_chats.add(packet.chat_id)
                    chat_title = packet.chat_title or f"群組 {packet.chat_id}"
                    text += f"\n{i}. {chat_title}"
                    # 保存到 context 以便後續使用
                    if 'recent_groups' not in context.user_data:
                        context.user_data['recent_groups'] = []
                    context.user_data['recent_groups'].append({
                        'chat_id': packet.chat_id,
                        'title': chat_title
                    })
        
        # 在会话内完成所有操作后再发送消息
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
        )


async def show_group_selection(query, db_user, context):
    """顯示群組選擇"""
    packet_data = context.user_data.get('send_packet', {})
    
    # 在會話內獲取用戶發過紅包的群組，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            try:
                await query.edit_message_text("發生錯誤，請稍後再試")
            except:
                if hasattr(query, 'message') and query.message:
                    await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内查询红包（最近发送的群组）
        packets = db.query(RedPacket).filter(
            RedPacket.sender_id == user.id
        ).order_by(RedPacket.created_at.desc()).limit(10).all()
        
        # 查询最近发送给的用户（通过RedPacketClaim）
        from shared.database.models import RedPacketClaim
        recent_claims = db.query(RedPacketClaim).join(RedPacket).filter(
            RedPacket.sender_id == user.id
        ).order_by(RedPacketClaim.claimed_at.desc()).limit(10).all()
        
        text = f"""
➕ *發紅包 - 選擇群組或用戶*

*紅包信息：*
• 幣種：{packet_data.get('currency', 'usdt').upper()}
• 類型：{"手氣最佳" if packet_data.get('packet_type') == "random" else "紅包炸彈"}
• 金額：{packet_data.get('amount')} {packet_data.get('currency', 'usdt').upper()}
• 數量：{packet_data.get('count')} 份
• 祝福語：{packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)}

*方式一：* 在群組中使用命令
在目標群組中輸入：`/send <金額> <數量> [祝福語]`

*方式二：* 選擇已發過紅包的群組或用戶
"""
        
        keyboard = []
        
        # 在会话内访问packet属性
        seen_chats = set()
        seen_users = set()
        
        # 添加最近发送的群组
        for packet in packets[:5]:
            if packet.chat_id and packet.chat_id not in seen_chats:
                seen_chats.add(packet.chat_id)
                chat_title = packet.chat_title or f"群組 {packet.chat_id}"
                
                # 生成callback_data，确保不超过64字节限制
                # 使用简化的message标志（'default'或'custom'）而不是完整消息
                msg_flag = 'default' if packet_data.get('message') == PacketConstants.DEFAULT_MESSAGE else 'custom'
                bomb_num_str = str(packet_data.get('bomb_number', '')) if packet_data.get('bomb_number') is not None else ''
                
                # 构建callback_data
                callback_data = f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{bomb_num_str}:{msg_flag}:{packet.chat_id}"
                
                # 如果超过64字节，使用更短的格式（不包含message和bomb_number）
                if len(callback_data) > 64:
                    callback_data = f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{packet.chat_id}"
                    # 将message和bomb_number存储在context中
                    if 'pending_confirm' not in context.user_data:
                        context.user_data['pending_confirm'] = {}
                    context.user_data['pending_confirm'][str(packet.chat_id)] = {
                        'bomb_number': packet_data.get('bomb_number'),
                        'message': packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
                    }
                    logger.debug(f"Callback data too long ({len(callback_data)} bytes), using simplified format for chat_id {packet.chat_id}")
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"📱 {chat_title[:20]}",
                        callback_data=callback_data
                    ),
                ])
        
        # 添加最近发送给的用户（个人聊天）
        for claim in recent_claims[:3]:  # 最多显示3个用户
            if claim.user_id and claim.user_id not in seen_users:
                seen_users.add(claim.user_id)
                # 查询用户信息
                claim_user = db.query(User).filter(User.id == claim.user_id).first()
                if claim_user:
                    user_display = claim_user.first_name or claim_user.username or f"用戶 {claim_user.tg_id}"
                    # 使用用户的tg_id作为chat_id（个人聊天）
                    user_chat_id = claim_user.tg_id
                    
                    # 生成callback_data
                    msg_flag = 'default' if packet_data.get('message') == PacketConstants.DEFAULT_MESSAGE else 'custom'
                    bomb_num_str = str(packet_data.get('bomb_number', '')) if packet_data.get('bomb_number') is not None else ''
                    callback_data = f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{bomb_num_str}:{msg_flag}:{user_chat_id}"
                    
                    # 如果超过64字节，使用简化格式
                    if len(callback_data) > 64:
                        callback_data = f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{user_chat_id}"
                        if 'pending_confirm' not in context.user_data:
                            context.user_data['pending_confirm'] = {}
                        context.user_data['pending_confirm'][str(user_chat_id)] = {
                            'bomb_number': packet_data.get('bomb_number'),
                            'message': packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
                        }
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            f"👤 {user_display[:18]}",
                            callback_data=callback_data
                        ),
                    ])
        
        # 同样处理group_input的callback_data
        msg_flag = 'default' if packet_data.get('message') == PacketConstants.DEFAULT_MESSAGE else 'custom'
        bomb_num_str = str(packet_data.get('bomb_number', '')) if packet_data.get('bomb_number') is not None else ''
        group_input_callback = f"packets:send:group_input:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{bomb_num_str}:{msg_flag}"
        
        # 如果超过64字节，使用更短的格式
        if len(group_input_callback) > 64:
            group_input_callback = f"packets:send:group_input:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}"
            logger.debug(f"Group input callback data too long, using simplified format")
        
        keyboard.append([
            InlineKeyboardButton("📝 輸入群組鏈接/ID", callback_data=group_input_callback),
        ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
        ])
        
        # 在会话内完成所有操作后再发送消息
        # 检查消息是否需要更新，避免"Message is not modified"错误
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                await query.answer("已顯示", show_alert=False)
                logger.debug(f"Message not modified in show_group_selection, user {db_user.tg_id}")
            elif "Button_data_invalid" in error_msg or ("button" in error_msg.lower() and "invalid" in error_msg.lower()):
                # callback_data可能有问题，尝试使用简化的键盘
                logger.error(f"Button_data_invalid error in show_group_selection: {e}", exc_info=True)
                # 重新生成简化的键盘
                simplified_keyboard = []
                seen_chats_simple = set()
                for packet in packets[:3]:  # 只显示前3个，减少callback_data长度
                    if packet.chat_id and packet.chat_id not in seen_chats_simple:
                        seen_chats_simple.add(packet.chat_id)
                        chat_title = packet.chat_title or f"群組 {packet.chat_id}"
                        # 使用最短的callback_data
                        simple_callback = f"packets:send:confirm:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{packet.chat_id}"
                        if len(simple_callback) <= 64:
                            simplified_keyboard.append([
                                InlineKeyboardButton(
                                    f"📱 {chat_title[:15]}",
                                    callback_data=simple_callback
                                ),
                            ])
                            # 存储完整数据到context
                            if 'pending_confirm' not in context.user_data:
                                context.user_data['pending_confirm'] = {}
                            context.user_data['pending_confirm'][str(packet.chat_id)] = {
                                'bomb_number': packet_data.get('bomb_number'),
                                'message': packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
                            }
                simplified_keyboard.append([
                    InlineKeyboardButton("📝 輸入群組", callback_data=f"packets:send:group_input:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}"),
                ])
                simplified_keyboard.append([
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ])
                try:
                    await query.edit_message_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(simplified_keyboard),
                    )
                except Exception as e2:
                    logger.error(f"Error with simplified keyboard: {e2}", exc_info=True)
                    await query.answer("發生錯誤，請稍後再試", show_alert=True)
            else:
                logger.error(f"Error editing message in show_group_selection: {e}", exc_info=True)
                raise


async def show_group_link_input(query, db_user, context):
    """顯示群組鏈接輸入提示 - 支持只输入用户名（自动补全）"""
    packet_data = context.user_data.get('send_packet', {})
    
    text = """
➕ *發紅包 - 輸入群組*

請輸入群組 ID 或群組用戶名：

*方式一：* 輸入群組 ID（數字）
例如：`-1001234567890`

*方式二：* 輸入群組用戶名（自動補全 @ 和 t.me/）
例如：`groupname` 或 `@groupname` 或 `https://t.me/groupname`

💡 提示：
• 可以直接輸入用戶名（如：`minihb2`），系統會自動補全
• 也可以在目標群組中直接使用命令 `/send <金額> <數量> [祝福語]`
"""
    
    keyboard = [
        [
            InlineKeyboardButton("◀️ 返回", callback_data=f"packets:send:group:{packet_data['currency']}:{packet_data['packet_type']}:{packet_data['amount']}:{packet_data['count']}:{packet_data.get('bomb_number', '')}:{packet_data.get('message', 'default')}"),
        ],
    ]
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        error_msg = str(e)
        if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
            await query.answer("已顯示輸入提示", show_alert=False)
        else:
            raise
    
    # 設置狀態，等待用戶輸入
    context.user_data['waiting_for_group'] = True


async def confirm_and_send_packet(query, db_user, context):
    """確認並發送紅包"""
    packet_data = context.user_data.get('send_packet', {})
    
    currency = packet_data.get('currency', 'usdt')
    packet_type = packet_data.get('packet_type', 'random')
    amount = Decimal(str(packet_data.get('amount', 0)))
    count = int(packet_data.get('count', 1))
    bomb_number = packet_data.get('bomb_number')
    message = packet_data.get('message', PacketConstants.DEFAULT_MESSAGE)
    chat_id = packet_data.get('chat_id')
    
    # 在会话内查询用户以确保数据最新
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await query.answer("發生錯誤，請稍後再試", show_alert=True)
            return
        
        # 使用安全工具驗證
        from bot.utils.security import validate_amount, validate_packet_count
        
        # 獲取餘額（在會話內）
        balance = Decimal(str(getattr(user, f"balance_{currency}", 0) or 0))
        
        # 驗證金額
        is_valid, error_msg = validate_amount(str(amount), currency, balance)
        if not is_valid:
            await query.answer(error_msg, show_alert=True)
            return
        
        # 驗證數量
        is_valid, error_msg = validate_packet_count(count, packet_type)
        if not is_valid:
            await query.answer(error_msg, show_alert=True)
            return
        
        # 檢查餘額（在會話內）
        if balance < amount:
            await query.answer(f"餘額不足，當前 {currency.upper()} 餘額: {float(balance):.4f}", show_alert=True)
            return
    
    # 如果沒有選擇群組，提示用戶輸入群組ID
    if not chat_id:
        text = f"""
✅ *紅包已準備好！*

*紅包信息：*
• 幣種：{currency.upper()}
• 類型：{"手氣最佳" if packet_type == "random" else "紅包炸彈"}
• 金額：{float(amount):.2f} {currency.upper()}
• 數量：{count} 份
{f"• 炸彈數字：{bomb_number}" if bomb_number is not None else ""}
• 祝福語：{message}

*請選擇或輸入群組：*
"""
        
        # 獲取用戶發過紅包的群組
        # 注意：User 已在文件頂部導入，不再重複導入
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            if user:
                packets = db.query(RedPacket).filter(
                    RedPacket.sender_id == user.id
                ).order_by(RedPacket.created_at.desc()).limit(5).all()
                
                keyboard = []
                seen_chats = set()
                for packet in packets:
                    if packet.chat_id and packet.chat_id not in seen_chats:
                        seen_chats.add(packet.chat_id)
                        chat_title = packet.chat_title or f"群組 {packet.chat_id}"
                        keyboard.append([
                            InlineKeyboardButton(
                                f"📱 {chat_title[:20]}",
                                callback_data=f"packets:send:confirm:{currency}:{packet_type}:{amount}:{count}:{bomb_number or ''}:{message}:{packet.chat_id}"
                            ),
                        ])
                
                keyboard.append([
                    InlineKeyboardButton(
                        "📝 輸入群組 ID/鏈接",
                        callback_data=f"packets:send:group_input:{currency}:{packet_type}:{amount}:{count}:{bomb_number or ''}:{message}"
                    ),
                ])
                
                keyboard.append([
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ])
            else:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "📝 輸入群組 ID/鏈接",
                            callback_data=f"packets:send:group_input:{currency}:{packet_type}:{amount}:{count}:{bomb_number or ''}:{message}"
                        ),
                    ],
                    [
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                    ],
                ]
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    
    # ========================================
    # 检查机器人和发送者是否在群组中（必须通过才能创建红包）
    # ========================================
    bot_in_group = False
    sender_in_group = False
    
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        bot = Bot(token=settings.BOT_TOKEN)
        sender_tg_id = db_user.tg_id
        
        # 检查机器人是否在群组中
        try:
            # 先獲取機器人信息
            bot_info = await bot.get_me()
            bot_member = await bot.get_chat_member(chat_id, bot_info.id)
            bot_status = bot_member.status
            if bot_status in ['left', 'kicked']:
                # 机器人不在群组中
                await query.edit_message_text(
                    f"""❌ *機器人不在群組中*

機器人需要先加入群組才能發送紅包。

*解決方案：*
1. 在群組中添加機器人 @{settings.BOT_USERNAME or 'luckyred2025_bot'}
2. 確保機器人有發送消息的權限
3. 然後重新嘗試發送紅包

*群組 ID：* `{chat_id}`""",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
                    ]])
                )
                return
            bot_in_group = True
            logger.info(f"Bot is in group {chat_id}, status: {bot_status}")
        except TelegramError as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg or "bot is not a member" in error_msg or "forbidden" in error_msg:
                await query.edit_message_text(
                    f"""❌ *機器人不在群組中*

機器人需要先加入群組才能發送紅包。

*解決方案：*
1. 確認群組 ID 正確：`{chat_id}`
2. 在群組中添加機器人 @{settings.BOT_USERNAME or 'luckyred2025_bot'}
3. 確保機器人有發送消息的權限

💡 *如何添加機器人到群組：*
• 打開群組設置 → 添加成員 → 搜索機器人""",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
                    ]])
                )
                return
            else:
                # 其他錯誤也要阻止創建紅包
                logger.warning(f"Error checking bot membership: {e}")
                await query.edit_message_text(
                    f"""❌ *無法驗證機器人權限*

檢查機器人群組權限時出錯。

*請確保：*
1. 機器人已加入群組
2. 機器人有發送消息的權限

*群組 ID：* `{chat_id}`
*錯誤：* {str(e)[:100]}""",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
                    ]])
                )
                return
        
        # 检查发送者是否在群组中（必须通过）
        try:
            sender_member = await bot.get_chat_member(chat_id, sender_tg_id)
            sender_status = sender_member.status
            if sender_status in ['left', 'kicked']:
                await query.edit_message_text(
                    f"""❌ *您不在目標群組中*

您需要先加入群組才能發送紅包到該群組。

*解決方案：*
1. 加入群組
2. 然後重新嘗試發送紅包

*群組 ID：* `{chat_id}`""",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
                    ]])
                )
                return
            sender_in_group = True
            logger.info(f"Sender {sender_tg_id} is in group {chat_id}, status: {sender_status}")
        except TelegramError as e:
            # 发送者不在群组，阻止发送
            error_msg = str(e).lower()
            if "user not found" in error_msg or "forbidden" in error_msg:
                await query.edit_message_text(
                    f"""❌ *您不在目標群組中*

您需要先加入群組才能發送紅包。

*解決方案：*
1. 加入群組 `{chat_id}`
2. 然後重新嘗試發送紅包""",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
                    ]])
                )
                return
            logger.warning(f"Could not verify sender membership: {e}")
            # 如果無法驗證，繼續嘗試（可能是私人群組等情況）
            sender_in_group = True
    except Exception as e:
        logger.error(f"Error checking group membership: {e}", exc_info=True)
        await query.edit_message_text(
            f"""❌ *檢查群組權限失敗*

無法驗證群組成員資格，請稍後再試。

*錯誤：* {str(e)[:100]}""",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
            ]])
        )
        return
    
    # 最終檢查
    if not bot_in_group:
        await query.edit_message_text(
            f"""❌ *機器人不在群組中*

請先將機器人添加到群組 `{chat_id}`""",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ 返回", callback_data="menu:packets")
            ]])
        )
        return
    
    # 創建紅包
    try:
        from bot.utils.api_client import get_api_client
        from bot.utils.security import sanitize_message
        from bot.utils.ui_helpers import show_loading
        
        # 顯示加載狀態
        await show_loading(query, "正在發送紅包...")
        
        # 清理消息
        message = sanitize_message(message)
        
        # 使用統一的 API 客戶端
        from bot.utils.logging_helpers import log_packet_action
        
        api_client = get_api_client()
        
        # 在会话外使用db_user.tg_id（基本属性，不会触发会话问题）
        sender_tg_id = db_user.tg_id
        
        # 获取chat_title（如果是群组，尝试获取群组名称）
        chat_title = None
        try:
            from telegram import Bot
            bot = Bot(token=settings.BOT_TOKEN)
            chat = await bot.get_chat(chat_id)
            chat_title = chat.title if hasattr(chat, 'title') else None
        except Exception as e:
            logger.debug(f"Could not get chat title for {chat_id}: {e}")
            # 如果无法获取，使用chat_id作为标题
            chat_title = f"群組 {chat_id}" if chat_id < 0 else None
        
        result = await api_client.post(
            "/redpackets/create",
            data={
                "currency": currency,
                "packet_type": packet_type,
                "total_amount": float(amount),
                "total_count": count,
                "message": message,
                "chat_id": chat_id,
                "chat_title": chat_title,
                "bomb_number": bomb_number,
            },
            tg_id=sender_tg_id
        )
        
        # 記錄紅包操作
        log_packet_action(
            user_id=sender_tg_id,
            action="create",
            packet_id=result.get('id'),
            amount=float(amount),
            currency=currency,
            success=True
        )
        
        # 清除用戶緩存（因為餘額已更新）
        from bot.utils.cache import UserCache
        UserCache.invalidate(sender_tg_id)
        
        # ✅ 發送紅包消息到群組
        packet_uuid = result.get('uuid', '')
        try:
            from telegram import Bot
            bot = Bot(token=settings.BOT_TOKEN)
            
            # 構建群組中的紅包消息
            type_text = "🎲 手氣最佳" if packet_type == "random" else "💣 紅包炸彈"
            group_message = f"""
🧧 *{message}*

{type_text}
💰 金額：{float(amount):.2f} {currency.upper()}
👥 數量：{count} 份

🎁 點擊下方按鈕搶紅包！
"""
            # 構建搶紅包按鈕
            claim_keyboard = [[
                InlineKeyboardButton(
                    "🧧 搶紅包",
                    url=f"{settings.MINIAPP_URL}/claim/{packet_uuid}"
                )
            ]]
            
            await bot.send_message(
                chat_id=chat_id,
                text=group_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(claim_keyboard)
            )
            logger.info(f"Red packet message sent to group {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send red packet message to group {chat_id}: {e}")
            # 群組發送失敗不影響紅包創建成功
        
        # 使用輔助函數格式化信息
        packet_info = format_packet_info(currency, packet_type, amount, count, bomb_number, message)
        
        text = f"""
✅ *紅包發送成功！*

*紅包信息：*
{packet_info}
• UUID: `{packet_uuid}`

紅包已發送到群組！
"""
        
        # 检查是否应该使用内联按钮
        use_inline = context.user_data.get('use_inline_buttons', False)
        
        if use_inline:
            # 使用内联按钮
            keyboard = [
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # 使用底部键盘（通过新消息发送）
            from bot.keyboards.reply_keyboards import get_packets_reply_keyboard
            if hasattr(query, 'message') and query.message:
                await query.message.reply_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=get_packets_reply_keyboard(),
                )
            else:
                # 如果无法发送新消息，尝试编辑
                keyboard = [
                    [
                        InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                    ],
                ]
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        
        # 清除临时数据
        context.user_data.pop('send_packet', None)
        context.user_data.pop('waiting_for_group', None)
        context.user_data.pop('waiting_for_message', None)
        context.user_data.pop('send_packet_step', None)
        context.user_data.pop('use_inline_buttons', None)
        return
    except Exception as e:
        logger.error(f"Error sending packet: {e}", exc_info=True)
        error_msg = str(e)
        
        # 更详细的错误处理
        if "餘額不足" in error_msg or "Insufficient balance" in error_msg:
            error_msg = "餘額不足"
        elif "connection" in error_msg.lower() or "Connection" in error_msg or "All connection attempts failed" in error_msg:
            # API 连接失败
            from shared.config.settings import get_settings
            api_settings = get_settings()
            error_msg = f"無法連接到 API 服務器\n\n請檢查：\n• API 服務器是否運行中\n• API URL: `{api_settings.API_BASE_URL}`\n• 網絡連接是否正常\n\n💡 提示：請確保後端 API 服務器已啟動"
        elif "HTTP" in error_msg or "Request" in error_msg:
            error_msg = "網絡錯誤，請稍後再試"
        elif "timeout" in error_msg.lower():
            error_msg = "請求超時，請稍後再試"
        
        # 記錄失敗操作
        log_packet_action(
            user_id=db_user.tg_id,
            action="create",
            amount=float(amount),
            currency=currency,
            success=False
        )
        
        text = f"""
❌ *發送失敗*

錯誤：{error_msg}

請重試或使用 miniapp 發送
"""
    
    # 检查是否应该使用内联按钮
    use_inline = context.user_data.get('use_inline_buttons', False)
    
    if use_inline:
        # 使用内联按钮
        keyboard = [
            [
                InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
            ],
        ]
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        # 使用底部键盘（通过新消息发送，因为query可能来自内联按钮）
        from bot.keyboards.reply_keyboards import get_packets_reply_keyboard
        if hasattr(query, 'message') and query.message:
            await query.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_packets_reply_keyboard(),
            )
        else:
            # 如果无法发送新消息，尝试编辑
            keyboard = [
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
                ],
            ]
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    
    # 清除臨時數據
    context.user_data.pop('send_packet', None)
    context.user_data.pop('waiting_for_group', None)
    context.user_data.pop('waiting_for_message', None)


async def show_my_packets(query, db_user):
    """顯示我發送的紅包"""
    # 在會話內重新查詢用戶以確保數據最新，並在會話內完成所有操作
    # 注意：User 已在文件頂部導入，不再重複導入
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            try:
                await query.edit_message_text("發生錯誤，請稍後再試")
            except:
                if hasattr(query, 'message') and query.message:
                    await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 在会话内查询红包
        packets = db.query(RedPacket).filter(
            RedPacket.sender_id == user.id
        ).order_by(RedPacket.created_at.desc()).limit(10).all()
        
        # 在会话内访问packet属性
        if not packets:
            text = """
🎁 *我的紅包*

您還沒有發送過紅包

快去發一個吧！
"""
        else:
            text = "🎁 *我發送的紅包*\n\n"
            for i, packet in enumerate(packets[:5], 1):
                claimed = packet.claimed_count or 0
                total = packet.total_count
                status_emoji = "✅" if packet.status == RedPacketStatus.COMPLETED else "⏳" if packet.status == RedPacketStatus.ACTIVE else "❌"
                text += f"{status_emoji} {i}. {packet.message or PacketConstants.DEFAULT_MESSAGE}\n"
                text += f"   💰 {float(packet.total_amount):.2f} {packet.currency.value.upper()}\n"
                text += f"   👥 {claimed}/{total} 已領取\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "📱 查看完整記錄",
                    web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/packets")
                ),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data="menu:packets"),
            ],
        ]
        
        # 在会话内完成所有操作后再发送消息
        # 检查消息是否需要更新，避免"Message is not modified"错误
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg or "message is not modified" in error_msg.lower():
                await query.answer("已顯示", show_alert=False)
                logger.debug(f"Message not modified in show_amount_input, user {db_user.tg_id}")
            else:
                logger.error(f"Error editing message in show_amount_input: {e}", exc_info=True)
                raise
