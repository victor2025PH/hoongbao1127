"""
Lucky Red - 回覆鍵盤處理器
處理用戶點擊回覆鍵盤按鈕的操作
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from loguru import logger

from bot.keyboards.reply_keyboards import (
    get_main_reply_keyboard,
    get_wallet_reply_keyboard,
    get_packets_reply_keyboard,
    get_send_packet_currency_keyboard,
    get_send_packet_type_keyboard,
    get_send_packet_amount_keyboard,
    get_send_packet_count_keyboard,
    get_send_packet_group_keyboard,
    get_send_packet_confirm_keyboard,
    get_earn_reply_keyboard,
    get_game_reply_keyboard,
    get_profile_reply_keyboard,
    get_exchange_reply_keyboard,
    get_deposit_reply_keyboard,
    get_withdraw_reply_keyboard,
    remove_reply_keyboard,
)
from bot.utils.user_helpers import get_user_from_update
from bot.utils.query_helper import create_mock_query


async def handle_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理回覆鍵盤按鈕點擊"""
    try:
        if not update.message:
            return
        
        user_id = update.effective_user.id if update.effective_user else None
        logger.info(f"handle_reply_keyboard called for user {user_id}")
        
        # 如果不是文本消息（如附件、照片等），檢查是否在等待輸入
        if not update.message.text:
            # 檢查是否在等待用戶輸入（群組 ID/祝福語等）
            if context.user_data.get('waiting_for_group') or context.user_data.get('waiting_for_message'):
                from bot.handlers.packets import handle_text_input
                await handle_text_input(update, context)
            else:
                # 如果不在等待輸入狀態，忽略非文本消息（如附件按鈕點擊）
                # 不返回上一級，保持當前狀態
                logger.debug(f"Ignoring non-text message from user {user_id}")
            return
        
        text = update.message.text.strip()
        logger.info(f"User {user_id} clicked button: '{text}'")
        
        db_user = await get_user_from_update(update, context)
        if not db_user:
            logger.warning(f"User {user_id} not found in database")
            await update.message.reply_text("請先使用 /start 註冊", reply_markup=get_main_reply_keyboard())
            return
    except Exception as e:
        logger.error(f"Error in handle_reply_keyboard (initial): {e}", exc_info=True)
        try:
            if update.message:
                await update.message.reply_text("發生錯誤，請稍後再試", reply_markup=get_main_reply_keyboard())
        except:
            pass
        return
    
    # 檢查是否在等待用戶輸入（金額、數量、群組 ID/祝福語等）
    # 优先检查，避免被其他处理器拦截
    # 添加调试日志
    waiting_for_group = context.user_data.get('waiting_for_group', False)
    waiting_for_message = context.user_data.get('waiting_for_message', False)
    send_packet_step = context.user_data.get('send_packet_step')
    
    if waiting_for_group or waiting_for_message or send_packet_step in ['amount_input', 'count_input', 'group_input', 'bind_group']:
        logger.info(f"User {user_id} is in input state: waiting_for_group={waiting_for_group}, waiting_for_message={waiting_for_message}, step={send_packet_step}, text='{text}'")
        from bot.handlers.packets import handle_text_input
        await handle_text_input(update, context)
        return
    
    # 主菜單按鈕
    if text == "💰 錢包":
        logger.info(f"User {user_id} clicked '💰 錢包' button")
        try:
            # 在会话内重新查询用户以确保数据最新
            from shared.database.connection import get_db
            from shared.database.models import User
            from bot.handlers.menu import show_wallet_menu
            
            with get_db() as db:
                user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
                if not user:
                    await update.message.reply_text("發生錯誤，請稍後再試")
                    return
                
                query = create_mock_query(update)
                await show_wallet_menu(query, user)
            
            await update.message.reply_text(
                "選擇操作：",
                reply_markup=get_wallet_reply_keyboard(),
            )
            logger.info(f"Successfully handled '💰 錢包' button for user {user_id}")
        except Exception as e:
            logger.error(f"Error handling '💰 錢包' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("處理消息時發生錯誤，請稍後再試或使用/start 重新開始")
        return
    
    elif text == "🧧 紅包":
        # 在会话内重新查询用户以确保数据最新
        from shared.database.connection import get_db
        from shared.database.models import User
        from bot.handlers.menu import show_packets_menu
        
        try:
            with get_db() as db:
                user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
                if not user:
                    await update.message.reply_text("發生錯誤，請稍後再試")
                    return
                
                query = create_mock_query(update)
                await show_packets_menu(query, user)
            
            await update.message.reply_text(
                "選擇操作：",
                reply_markup=get_packets_reply_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error handling '🧧 紅包' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("處理消息時發生錯誤，請稍後再試或使用/start 重新開始")
        return
    
    elif text == "📈 賺取":
        logger.info(f"User {user_id} clicked '📈 賺取' button")
        try:
            # 在会话内重新查询用户以确保数据最新
            from shared.database.connection import get_db
            from shared.database.models import User
            from bot.handlers.menu import show_earn_menu
            
            with get_db() as db:
                user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
                if not user:
                    await update.message.reply_text("發生錯誤，請稍後再試")
                    return
                
                query = create_mock_query(update)
                await show_earn_menu(query, user)
            
            await update.message.reply_text(
                "選擇操作：",
                reply_markup=get_earn_reply_keyboard(),
            )
            logger.info(f"Successfully handled '📈 賺取' button for user {user_id}")
        except Exception as e:
            logger.error(f"Error handling '📈 賺取' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("處理消息時發生錯誤，請稍後再試或使用/start 重新開始")
        return
    
    elif text == "🎮 遊戲":
        logger.info(f"User {user_id} clicked '🎮 遊戲' button")
        try:
            from bot.handlers.menu import show_game_menu
            query = create_mock_query(update)
            await show_game_menu(query, db_user)
            await update.message.reply_text(
                "選擇遊戲：",
                reply_markup=get_game_reply_keyboard(),
            )
            logger.info(f"Successfully handled '🎮 遊戲' button for user {user_id}")
        except Exception as e:
            logger.error(f"Error handling '🎮 遊戲' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("發生錯誤，請稍後再試")
        return
    
    elif text == "👤 我的":
        logger.info(f"User {user_id} clicked '👤 我的' button")
        try:
            from bot.handlers.menu import show_profile_menu
            query = create_mock_query(update)
            await show_profile_menu(query, db_user)
            await update.message.reply_text(
                "選擇查看：",
                reply_markup=get_profile_reply_keyboard(),
            )
            logger.info(f"Successfully handled '👤 我的' button for user {user_id}")
        except Exception as e:
            logger.error(f"Error handling '👤 我的' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("發生錯誤，請稍後再試")
        return
    
    elif text == "🔄 切換模式" or text == "切换模式":
        # 处理模式切换（从键盘模式）- 显示三种模式选择
        from bot.handlers.mode_switch import show_mode_selection_from_keyboard
        await show_mode_selection_from_keyboard(update, context, db_user)
        return
    
    elif text == "📱 打開應用":
        from shared.config.settings import get_settings
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
        settings = get_settings()
        keyboard = [[
            InlineKeyboardButton(
                "🚀 打開 Lucky Red",
                web_app=WebAppInfo(url=settings.MINIAPP_URL)
            )
        ]]
        await update.message.reply_text(
            "點擊按鈕打開應用：",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    
    # 注意：由於所有回覆鍵盤按鈕現在都使用 web_app，它們會直接打開 miniapp
    # 不會觸發文本消息，所以這裡不需要處理這些按鈕
    # 但如果用戶直接輸入文本（非按鈕點擊），則返回主菜單
    
    # 返回主菜單
    elif text == "◀️ 返回主菜單":
        from bot.handlers.menu import show_main_menu
        query = create_mock_query(update)
        await show_main_menu(query, db_user)
        await update.message.reply_text(
            "已返回主菜單：",
            reply_markup=get_main_reply_keyboard(),
        )
        return
    
    # 錢包子菜單
    elif text == "💵 充值":
        await update.message.reply_text(
            "選擇充值幣種：",
            reply_markup=get_deposit_reply_keyboard(),
        )
        return
    
    elif text == "💸 提現":
        await update.message.reply_text(
            "選擇提現幣種：",
            reply_markup=get_withdraw_reply_keyboard(),
        )
        return
    
    elif text == "📜 交易記錄":
        from bot.handlers.wallet import show_transaction_history
        query = create_mock_query(update)
        await show_transaction_history(query, db_user)
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_wallet_reply_keyboard(),
        )
        return
    
    elif text == "🔄 兌換":
        from bot.handlers.wallet import show_exchange_menu
        query = create_mock_query(update)
        await show_exchange_menu(query, db_user)
        await update.message.reply_text(
            "選擇兌換類型：",
            reply_markup=get_exchange_reply_keyboard(),
        )
        return
    
    elif text == "◀️ 返回錢包":
        from bot.handlers.menu import show_wallet_menu
        query = create_mock_query(update)
        await show_wallet_menu(query, db_user)
        await update.message.reply_text(
            "已返回錢包：",
            reply_markup=get_wallet_reply_keyboard(),
        )
        return
    
    # 紅包子菜單
    elif text == "📋 查看紅包":
        from bot.handlers.packets import show_packets_list
        query = create_mock_query(update)
        await show_packets_list(query, db_user)
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_packets_reply_keyboard(),
        )
        return
    
    elif text == "➕ 發紅包":
        # 初始化發紅包數據
        context.user_data['send_packet'] = {}
        context.user_data['send_packet_step'] = 'currency'
        # 关键：明确标记这是底部键盘流程，不是内联按钮流程
        context.user_data['use_inline_buttons'] = False
        
        # 在会话内重新查询用户以确保数据最新
        from shared.database.connection import get_db
        from shared.database.models import User
        from bot.handlers.packets import show_send_packet_menu
        
        try:
            with get_db() as db:
                user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
                if not user:
                    await update.message.reply_text("發生錯誤，請稍後再試")
                    return
                
                query = create_mock_query(update)
                # ✅ 傳入 use_inline_buttons=False，使用底部鍵盤模式
                await show_send_packet_menu(query, user, use_inline_buttons=False)
            
            await update.message.reply_text(
                "選擇紅包幣種：",
                reply_markup=get_send_packet_currency_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error handling '➕ 發紅包' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("處理消息時發生錯誤，請稍後再試或使用/start 重新開始")
        return
    
    elif text == "🎁 我的紅包":
        # 在会话内重新查询用户以确保数据最新
        from shared.database.connection import get_db
        from shared.database.models import User
        from bot.handlers.packets import show_my_packets
        
        try:
            with get_db() as db:
                user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
                if not user:
                    await update.message.reply_text("發生錯誤，請稍後再試")
                    return
                
                query = create_mock_query(update)
                await show_my_packets(query, user)
            
            await update.message.reply_text(
                "選擇操作：",
                reply_markup=get_packets_reply_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error handling '🎁 我的紅包' button for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("處理消息時發生錯誤，請稍後再試或使用/start 重新開始")
        return
    
    # 賺取子菜單
    elif text == "📅 每日簽到":
        from bot.handlers.checkin import do_checkin_with_message
        await do_checkin_with_message(update.effective_user, update.message, is_callback=False)
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_earn_reply_keyboard(),
        )
        return
    
    elif text == "👥 邀請好友":
        from bot.handlers.start import invite_command
        await invite_command(update, context)
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_earn_reply_keyboard(),
        )
        return
    
    elif text == "🎯 任務中心":
        from bot.handlers.earn import show_tasks
        query = create_mock_query(update)
        await show_tasks(query, db_user)
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_earn_reply_keyboard(),
        )
        return
    
    elif text == "🎰 幸運轉盤":
        from shared.config.settings import get_settings
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
        settings = get_settings()
        keyboard = [[
            InlineKeyboardButton(
                "🎰 打開幸運轉盤",
                web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/lucky-wheel")
            )
        ]]
        await update.message.reply_text(
            "點擊按鈕打開幸運轉盤：",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        await update.message.reply_text(
            "選擇操作：",
            reply_markup=get_earn_reply_keyboard(),
        )
        return
    
    # 遊戲子菜單
    elif text == "🎰 金運局":
        from bot.handlers.game import show_gold_fortune_info
        query = create_mock_query(update)
        await show_gold_fortune_info(query, db_user)
        await update.message.reply_text(
            "選擇遊戲：",
            reply_markup=get_game_reply_keyboard(),
        )
        return
    
    elif text == "🎡 幸運轉盤":
        from bot.handlers.game import show_lucky_wheel_info
        query = create_mock_query(update)
        await show_lucky_wheel_info(query, db_user)
        await update.message.reply_text(
            "選擇遊戲：",
            reply_markup=get_game_reply_keyboard(),
        )
        return
    
    # 個人資料子菜單
    elif text == "📊 我的資料":
        from bot.handlers.profile import show_profile_info
        query = create_mock_query(update)
        await show_profile_info(query, db_user)
        await update.message.reply_text(
            "選擇查看：",
            reply_markup=get_profile_reply_keyboard(),
        )
        return
    
    elif text == "📈 統計數據":
        from bot.handlers.profile import show_profile_stats
        query = create_mock_query(update)
        await show_profile_stats(query, db_user)
        await update.message.reply_text(
            "選擇查看：",
            reply_markup=get_profile_reply_keyboard(),
        )
        return
    
    elif text == "⚙️ 設置":
        from bot.handlers.profile import show_profile_settings
        query = create_mock_query(update)
        await show_profile_settings(query, db_user)
        await update.message.reply_text(
            "選擇查看：",
            reply_markup=get_profile_reply_keyboard(),
        )
        return
    
    # 充值/提現幣種選擇
    elif text.startswith("💵 充值 ") or text.startswith("💸 提現 "):
        currency = text.split()[-1].lower()
        action = "deposit" if "充值" in text else "withdraw"
        from bot.handlers.wallet import handle_deposit, handle_withdraw_input
        query = create_mock_query(update)
        if action == "deposit":
            await handle_deposit(query, db_user, currency, context)
        else:
            await handle_withdraw_input(query, db_user, currency, context)
        return
    
    # 兌換類型
    elif "→" in text:
        parts = text.split("→")
        if len(parts) == 2:
            from_currency = parts[0].strip().lower()
            to_currency = parts[1].strip().lower()
            pair = f"{from_currency}_{to_currency}"
            from bot.handlers.wallet import handle_exchange_input
            query = create_mock_query(update)
            await handle_exchange_input(query, db_user, pair, context)
            return
    
    # ============================================
    # 發紅包流程處理
    # ============================================
    
    # 選擇幣種
    elif text.startswith("💵 發 ") or text == "⚡ 發能量紅包":
        if "USDT" in text:
            currency = "usdt"
        elif "TON" in text:
            currency = "ton"
        else:
            currency = "points"
        
        # 檢查餘額（在會話內）
        from shared.database.connection import get_db
        from shared.database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            if not user:
                await update.message.reply_text("發生錯誤，請稍後再試")
                return
            
            balance = float(getattr(user, f"balance_{currency}", 0) or 0)
        
        logger.info(f"User {db_user.tg_id} selected currency {currency}, balance: {balance}")
        
        # 如果餘額為 0，彈窗提醒
        if balance <= 0:
            currency_name = "USDT" if currency == "usdt" else "TON" if currency == "ton" else "能量"
            logger.info(f"User {db_user.tg_id} has insufficient balance for {currency}: {balance}")
            await update.message.reply_text(
                f"❌ *餘額不足*\n\n"
                f"您的 {currency_name} 餘額為 `{balance:.4f}`\n\n"
                f"請先充值後再發紅包！\n\n"
                f"*充值方式：*\n"
                f"• 點擊「💰 錢包」→「💵 充值」\n"
                f"• 或使用 miniapp 進行充值",
                parse_mode="Markdown",
                reply_markup=get_packets_reply_keyboard(),
            )
            return
        
        # 餘額充足，繼續流程
        context.user_data['send_packet'] = {'currency': currency}
        context.user_data['send_packet_step'] = 'type'
        
        # 直接發送類型選擇消息，不使用 show_packet_type_selection（避免 edit_message_text 問題）
        currency_upper = currency.upper()
        text = f"""
➕ *發紅包 - {currency_upper}*

*當前餘額：* `{balance:.4f}` {currency_upper}

*選擇紅包類型：*
• 🎲 手氣最佳 - 隨機金額分配，領取完成後金額最大的用戶將被標記為"最佳手氣"
• 💣 紅包炸彈 - 固定金額分配，如果領取金額的小數點後最後一位數字與炸彈數字相同，將觸發炸彈

請選擇類型：
"""
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_send_packet_type_keyboard(),
        )
        return
    
    # 選擇類型
    elif text == "🎲 手氣最佳":
        packet_data = context.user_data.get('send_packet', {})
        packet_data['packet_type'] = 'random'
        context.user_data['send_packet'] = packet_data
        context.user_data['send_packet_step'] = 'amount'
        
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        
        # 底部鍵盤模式 - 直接發送消息，不編輯舊消息
        # 獲取餘額
        from shared.database.connection import get_db
        from shared.database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            balance = float(getattr(user, f"balance_{currency}", 0) or 0) if user else 0
        
        await update.message.reply_text(
            f"➕ *發紅包 - {currency_upper} - 手氣最佳*\n\n"
            f"*當前餘額：* `{balance:.4f}` {currency_upper}\n\n"
            f"請選擇或輸入金額：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_amount_keyboard(currency, 'random'),
        )
        return
    
    elif text == "💣 紅包炸彈":
        packet_data = context.user_data.get('send_packet', {})
        packet_data['packet_type'] = 'equal'
        context.user_data['send_packet'] = packet_data
        context.user_data['send_packet_step'] = 'amount'
        
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        
        # 底部鍵盤模式 - 直接發送消息，不編輯舊消息
        from shared.database.connection import get_db
        from shared.database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            balance = float(getattr(user, f"balance_{currency}", 0) or 0) if user else 0
        
        await update.message.reply_text(
            f"➕ *發紅包 - {currency_upper} - 紅包炸彈*\n\n"
            f"*當前餘額：* `{balance:.4f}` {currency_upper}\n\n"
            f"請選擇或輸入金額：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_amount_keyboard(currency, 'equal'),
        )
        return
    
    # 選擇金額（從按鈕）
    elif text.startswith("💰 "):
        amount_str = text.replace("💰 ", "").strip()
        try:
            amount = float(amount_str)
            packet_data = context.user_data.get('send_packet', {})
            packet_data['amount'] = amount
            context.user_data['send_packet'] = packet_data
            context.user_data['send_packet_step'] = 'count'
            
            currency = packet_data.get('currency', 'usdt')
            currency_upper = currency.upper()
            packet_type = packet_data.get('packet_type', 'random')
            type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
            
            # 底部鍵盤模式 - 直接發送消息
            await update.message.reply_text(
                f"➕ *發紅包 - {currency_upper} - {type_text}*\n\n"
                f"*金額：* `{amount}` {currency_upper}\n\n"
                f"請選擇紅包數量（1-100）：",
                parse_mode="Markdown",
                reply_markup=get_send_packet_count_keyboard(currency, packet_type, str(amount)),
            )
            return
        except ValueError:
            pass
    
    # 自定義金額
    elif text == "📝 自定義金額":
        context.user_data['send_packet_step'] = 'amount_input'
        await update.message.reply_text(
            "請輸入紅包總金額（數字）：\n\n例如：100",
            reply_markup=ReplyKeyboardMarkup([[
                KeyboardButton("◀️ 取消")
            ]], resize_keyboard=True),
        )
        return
    
    # 選擇數量（從按鈕）
    elif text.startswith("📦 ") and "份" in text:
        count_str = text.replace("📦 ", "").replace(" 份", "").strip()
        try:
            count = int(count_str)
            packet_data = context.user_data.get('send_packet', {})
            packet_data['count'] = count
            context.user_data['send_packet'] = packet_data
            context.user_data['send_packet_step'] = 'group'
            
            currency = packet_data.get('currency', 'usdt')
            currency_upper = currency.upper()
            packet_type = packet_data.get('packet_type', 'random')
            type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
            amount = packet_data.get('amount', 0)
            message = packet_data.get('message', '恭喜發財！🧧')
            
            # 如果是紅包炸彈，需要設置炸彈數字
            if packet_type == 'equal':
                # 根據數量設置炸彈數字：5份=雙雷，10份=單雷
                if count == 5:
                    packet_data['bomb_number'] = None  # 雙雷，需要特殊處理
                elif count == 10:
                    packet_data['bomb_number'] = None  # 單雷，需要特殊處理
                context.user_data['send_packet'] = packet_data
            
            # 底部鍵盤模式 - 直接發送消息
            await update.message.reply_text(
                f"➕ *發紅包 - 選擇群組*\n\n"
                f"*紅包信息：*\n"
                f"• 幣種：{currency_upper}\n"
                f"• 類型：{type_text}\n"
                f"• 金額：{amount} {currency_upper}\n"
                f"• 數量：{count} 份\n"
                f"• 祝福語：{message}\n\n"
                f"請輸入群組 ID 或鏈接：",
                parse_mode="Markdown",
                reply_markup=get_send_packet_group_keyboard(),
            )
            return
        except ValueError:
            pass
    
    # 紅包炸彈特殊數量
    elif text == "5 份（雙雷）":
        packet_data = context.user_data.get('send_packet', {})
        packet_data['count'] = 5
        packet_data['bomb_number'] = None  # 雙雷
        context.user_data['send_packet'] = packet_data
        context.user_data['send_packet_step'] = 'group'
        
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        amount = packet_data.get('amount', 0)
        message = packet_data.get('message', '恭喜發財！🧧')
        
        # 底部鍵盤模式 - 直接發送消息
        await update.message.reply_text(
            f"➕ *發紅包 - 選擇群組*\n\n"
            f"*紅包信息：*\n"
            f"• 幣種：{currency_upper}\n"
            f"• 類型：紅包炸彈（5份雙雷）\n"
            f"• 金額：{amount} {currency_upper}\n"
            f"• 數量：5 份\n"
            f"• 祝福語：{message}\n\n"
            f"請輸入群組 ID 或鏈接：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_group_keyboard(),
        )
        return
    
    elif text == "10 份（單雷）":
        packet_data = context.user_data.get('send_packet', {})
        packet_data['count'] = 10
        packet_data['bomb_number'] = None  # 單雷
        context.user_data['send_packet'] = packet_data
        context.user_data['send_packet_step'] = 'group'
        
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        amount = packet_data.get('amount', 0)
        message = packet_data.get('message', '恭喜發財！🧧')
        
        # 底部鍵盤模式 - 直接發送消息
        await update.message.reply_text(
            f"➕ *發紅包 - 選擇群組*\n\n"
            f"*紅包信息：*\n"
            f"• 幣種：{currency_upper}\n"
            f"• 類型：紅包炸彈（10份單雷）\n"
            f"• 金額：{amount} {currency_upper}\n"
            f"• 數量：10 份\n"
            f"• 祝福語：{message}\n\n"
            f"請輸入群組 ID 或鏈接：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_group_keyboard(),
        )
        return
    
    # 自定義數量
    elif text == "📝 自定義數量":
        context.user_data['send_packet_step'] = 'count_input'
        await update.message.reply_text(
            "請輸入紅包數量（數字）：\n\n例如：20",
            reply_markup=ReplyKeyboardMarkup([[
                KeyboardButton("◀️ 取消")
            ]], resize_keyboard=True),
        )
        return
    
    # 查找群組
    elif text == "🔍 查找群組":
        from bot.handlers.packets import show_group_search
        query = create_mock_query(update)
        await show_group_search(query, db_user, context)
        await update.message.reply_text(
            "選擇已發過紅包的群組：",
            reply_markup=get_send_packet_group_keyboard(),
        )
        return
    
    # 綁定群組
    elif text == "📌 綁定群組":
        context.user_data['send_packet_step'] = 'bind_group'
        await update.message.reply_text(
            "請在目標群組中發送以下命令來綁定：\n\n`/bind`\n\n或者輸入群組 ID/鏈接：",
            reply_markup=ReplyKeyboardMarkup([[
                KeyboardButton("📝 輸入群組 ID"),
                KeyboardButton("◀️ 返回")
            ]], resize_keyboard=True),
        )
        return
    
    # 輸入群組 ID
    elif text == "📝 輸入群組 ID":
        context.user_data['send_packet_step'] = 'group_input'
        context.user_data['waiting_for_group'] = True
        # 关键：明确标记这是底部键盘流程
        context.user_data['use_inline_buttons'] = False
        await update.message.reply_text(
            "請輸入群組 ID 或鏈接：\n\n例如：-1001234567890\n或：https://t.me/groupname\n或：@groupname",
            reply_markup=ReplyKeyboardMarkup([[
                KeyboardButton("◀️ 取消")
            ]], resize_keyboard=True),
        )
        return
    
    # 返回按鈕處理
    elif text == "◀️ 返回紅包":
        context.user_data.pop('send_packet', None)
        context.user_data.pop('send_packet_step', None)
        from bot.handlers.menu import show_packets_menu
        query = create_mock_query(update)
        await show_packets_menu(query, db_user)
        await update.message.reply_text(
            "已返回紅包菜單：",
            reply_markup=get_packets_reply_keyboard(),
        )
        return
    
    elif text == "◀️ 返回幣種":
        context.user_data['send_packet'] = {}
        context.user_data['send_packet_step'] = 'currency'
        # 確保標記為底部鍵盤模式
        context.user_data['use_inline_buttons'] = False
        from bot.handlers.packets import show_send_packet_menu
        query = create_mock_query(update)
        await show_send_packet_menu(query, db_user, use_inline_buttons=False)
        await update.message.reply_text(
            "選擇紅包幣種：",
            reply_markup=get_send_packet_currency_keyboard(),
        )
        return
    
    elif text == "◀️ 返回類型":
        packet_data = context.user_data.get('send_packet', {})
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        context.user_data['send_packet_step'] = 'type'
        
        # 底部鍵盤模式 - 直接發送消息
        from shared.database.connection import get_db
        from shared.database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            balance = float(getattr(user, f"balance_{currency}", 0) or 0) if user else 0
        
        await update.message.reply_text(
            f"➕ *發紅包 - {currency_upper}*\n\n"
            f"*當前餘額：* `{balance:.4f}` {currency_upper}\n\n"
            f"請選擇紅包類型：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_type_keyboard(),
        )
        return
    
    elif text == "◀️ 返回金額":
        packet_data = context.user_data.get('send_packet', {})
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        packet_type = packet_data.get('packet_type', 'random')
        type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
        context.user_data['send_packet_step'] = 'amount'
        
        # 底部鍵盤模式 - 直接發送消息
        from shared.database.connection import get_db
        from shared.database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
            balance = float(getattr(user, f"balance_{currency}", 0) or 0) if user else 0
        
        await update.message.reply_text(
            f"➕ *發紅包 - {currency_upper} - {type_text}*\n\n"
            f"*當前餘額：* `{balance:.4f}` {currency_upper}\n\n"
            f"請選擇或輸入金額：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_amount_keyboard(currency, packet_type),
        )
        return
    
    elif text == "◀️ 返回數量":
        packet_data = context.user_data.get('send_packet', {})
        currency = packet_data.get('currency', 'usdt')
        currency_upper = currency.upper()
        packet_type = packet_data.get('packet_type', 'random')
        type_text = "手氣最佳" if packet_type == "random" else "紅包炸彈"
        amount = packet_data.get('amount', 0)
        context.user_data['send_packet_step'] = 'count'
        
        # 底部鍵盤模式 - 直接發送消息
        await update.message.reply_text(
            f"➕ *發紅包 - {currency_upper} - {type_text}*\n\n"
            f"*金額：* `{amount}` {currency_upper}\n\n"
            f"請選擇紅包數量：",
            parse_mode="Markdown",
            reply_markup=get_send_packet_count_keyboard(currency, packet_type, str(amount)),
        )
        return
    
    # 確認發送
    elif text == "✅ 確認發送":
        from bot.handlers.packets import confirm_and_send_from_message
        try:
            await confirm_and_send_from_message(update, db_user, context)
            # 清理狀態
            context.user_data.pop('send_packet', None)
            context.user_data.pop('send_packet_step', None)
            await update.message.reply_text(
                "已返回紅包菜單：",
                reply_markup=get_packets_reply_keyboard(),
            )
        except Exception as e:
            logger.error(f"Error in confirm_and_send_from_message: {e}", exc_info=True)
            await update.message.reply_text(
                f"發送失敗：{str(e)}",
                reply_markup=get_packets_reply_keyboard(),
            )
        return
    
    # 處理用戶輸入的金額、數量、群組 ID
    elif context.user_data.get('send_packet_step') in ['amount_input', 'count_input', 'group_input', 'bind_group']:
        from bot.handlers.packets import handle_text_input
        await handle_text_input(update, context)
        return
    
    # 取消
    elif text == "◀️ 取消":
        context.user_data.pop('send_packet', None)
        context.user_data.pop('send_packet_step', None)
        context.user_data.pop('waiting_for_group', None)
        context.user_data.pop('waiting_for_message', None)
        await update.message.reply_text(
            "已取消發紅包",
            reply_markup=get_packets_reply_keyboard(),
        )
        return
    
    # 未匹配的按鈕 - 記錄並提示用戶
    else:
        logger.warning(f"Unhandled button text from user {user_id}: '{text}'")
        # 检查是否可能是群组输入（用户名格式）
        # 如果包含字母、数字、下划线，可能是群组用户名
        import re
        if re.match(r'^[a-zA-Z0-9_]+$', text) and len(text) > 2:
            # 可能是群组用户名，检查是否在发送红包流程中
            if context.user_data.get('send_packet'):
                logger.info(f"Detected potential group username '{text}', attempting to process as group input")
                # 尝试设置为群组输入状态并处理
                context.user_data['waiting_for_group'] = True
                context.user_data['send_packet_step'] = 'group_input'
                # 关键：明确标记这是底部键盘流程
                context.user_data['use_inline_buttons'] = False
                from bot.handlers.packets import handle_text_input
                await handle_text_input(update, context)
                return
        
        # 檢查是否可能是數字輸入（金額或數量）
        try:
            # 嘗試解析為數字
            num_value = float(text)
            # 如果解析成功，可能是用戶在輸入金額或數量
            # 但這應該已經被 handle_text_input 處理了
            # 如果到這裡，說明狀態可能有問題
            logger.warning(f"User {user_id} sent number '{text}' but not in input step")
        except ValueError:
            pass
        
        # 嘗試返回主菜單
        try:
            from bot.utils.i18n import t
            await update.message.reply_text(
                t("unrecognized", user=db_user),
                reply_markup=get_main_reply_keyboard(),
            )
            from bot.handlers.menu import show_main_menu
            query = create_mock_query(update)
            await show_main_menu(query, db_user)
        except Exception as e:
            logger.error(f"Error handling unhandled button: {e}", exc_info=True)
            try:
                from bot.utils.i18n import t
                await update.message.reply_text(
                    t("restart", user=db_user),
                    reply_markup=get_main_reply_keyboard(),
                )
            except:
                pass
