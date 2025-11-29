"""
Lucky Red - 開始/幫助處理器
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from loguru import logger

from shared.config.settings import get_settings
from shared.database.connection import get_db
from shared.database.models import User
from bot.utils.user_helpers import get_or_create_user
from bot.utils.logging_helpers import log_user_action

settings = get_settings()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    user = update.effective_user
    
    # 處理邀請碼
    invite_code = None
    if context.args and len(context.args) > 0:
        invite_code = context.args[0]
    
    # 使用統一的用戶獲取函數
    db_user = await get_or_create_user(
        tg_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        use_cache=False  # 註冊時不使用緩存，確保數據最新
    )
    
    # 在會話內獲取 invited_by 狀態（避免會話分離錯誤）
    with get_db() as db:
        # 重新查詢用戶以確保在會話內
        db_user_refreshed = db.query(User).filter(User.tg_id == user.id).first()
        if not db_user_refreshed:
            logger.error(f"User {user.id} not found after creation")
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        is_new_user = not db_user_refreshed.invited_by
        
        # 處理邀請關係
        if invite_code and not db_user_refreshed.invited_by:
            inviter = db.query(User).filter(User.invite_code == invite_code).first()
            if inviter and inviter.tg_id != user.id:
                db_user_refreshed.invited_by = inviter.tg_id
                inviter.invite_count = (inviter.invite_count or 0) + 1
                db.commit()
                # 清除緩存
                from bot.utils.cache import UserCache
                UserCache.invalidate(inviter.tg_id)
                UserCache.invalidate(user.id)
                logger.info(f"User {user.id} invited by {inviter.tg_id}")
                log_user_action(user.id, "invited", {"inviter_id": inviter.tg_id, "invite_code": invite_code})
                is_new_user = False  # 更新狀態
        
        # 記錄用戶操作（在會話內完成）
        log_user_action(user.id, "start", {"is_new": is_new_user})
    logger.info(f"User {user.id} ({user.username}) sent /start command")
    
    # 構建歡迎消息
    welcome_text = f"""
🧧 *歡迎來到 Lucky Red 搶紅包！*

Hi {user.first_name}！

這裡是最有趣的紅包遊戲平台：
• 💰 發紅包給群友
• 🎁 搶紅包贏大獎
• 📅 每日簽到領積分
• 👥 邀請好友得返佣

快來試試吧！👇
"""
    
    # 使用主回覆鍵盤和內聯鍵盤
    from bot.keyboards import get_main_menu
    from bot.keyboards.reply_keyboards import get_main_reply_keyboard
    
    try:
        # 先設置回覆鍵盤（在輸入框下方）- 這會一直顯示
        reply_keyboard = get_main_reply_keyboard()
        logger.info(f"Preparing to send reply keyboard to user {user.id}")
        logger.debug(f"Reply keyboard: {reply_keyboard}")
        
        result = await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_keyboard,  # 回覆鍵盤（在輸入框下方，一直顯示）
        )
        logger.info(f"✓ Reply keyboard sent successfully to user {user.id}, message_id: {result.message_id}")
    except Exception as e:
        logger.error(f"✗ Error sending reply keyboard to user {user.id}: {e}", exc_info=True)
        # 如果回覆鍵盤失敗，至少發送歡迎消息
        try:
            await update.message.reply_text(
                welcome_text,
                parse_mode="Markdown",
            )
            logger.info(f"✓ Fallback welcome message sent to user {user.id}")
        except Exception as e2:
            logger.error(f"✗ Failed to send fallback message: {e2}", exc_info=True)
    
    # 然後發送內聯鍵盤（在消息下方，可點擊）
    try:
        await update.message.reply_text(
            "💡 點擊下方按鈕或使用輸入框下方的菜單：",
            reply_markup=get_main_menu(),  # 內聯鍵盤（在消息下方）
        )
    except Exception as e:
        logger.error(f"Error sending inline keyboard: {e}", exc_info=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    help_text = """
🧧 *Lucky Red 使用指南*

*基本命令：*
/start - 開始使用
/wallet - 查看錢包餘額
/send - 發送紅包
/checkin - 每日簽到
/invite - 邀請好友

*如何發紅包：*
1. 在群組中輸入 /send
2. 選擇金額和數量
3. 發送紅包給群友

*如何搶紅包：*
點擊群組中的紅包消息即可搶

*每日簽到：*
連續簽到7天可獲得額外獎勵！

*邀請返佣：*
邀請好友可獲得其交易的10%返佣！

有問題？聯繫客服 @support
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /invite 命令"""
    from bot.utils.user_helpers import get_user_from_update
    from bot.utils.logging_helpers import log_user_action
    
    # 獲取用戶（帶緩存）
    db_user = await get_user_from_update(update, context)
    if not db_user:
        await update.message.reply_text("請先使用 /start 註冊")
        return
    
    # 在會話內處理邀請碼和獲取統計信息
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 生成邀請碼（如果沒有）
        if not user.invite_code:
            import secrets
            user.invite_code = secrets.token_urlsafe(8)
            db.commit()
            # 清除緩存
            from bot.utils.cache import UserCache
            UserCache.invalidate(user.tg_id)
        
        invite_code = user.invite_code
        invite_count = user.invite_count or 0
        invite_earnings = float(user.invite_earnings or 0)
    
    # 記錄操作
    log_user_action(db_user.tg_id, "invite_view")
    
    invite_link = f"https://t.me/{settings.BOT_USERNAME}?start={invite_code}"
    
    invite_text = f"""
👥 *邀請好友*

你的專屬邀請鏈接：
`{invite_link}`

📊 邀請統計：
• 已邀請：{invite_count} 人
• 累計收益：{invite_earnings:.2f} USDT

💡 邀請規則：
好友通過你的鏈接註冊後，你將獲得其所有交易的 10% 返佣！
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 分享給好友", url=f"https://t.me/share/url?url={invite_link}&text=快來玩搶紅包遊戲！")],
    ]
    
    await update.message.reply_text(
        invite_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

