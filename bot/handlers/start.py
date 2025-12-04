"""
Lucky Red - 開始/幫助處理器
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from loguru import logger

from shared.config.settings import get_settings
from shared.database.connection import get_db
from shared.database.models import User, Transaction, CurrencyType
from bot.utils.user_helpers import get_or_create_user
from bot.utils.logging_helpers import log_user_action
from bot.constants import InviteConstants
from decimal import Decimal

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
                
                # 發放邀請獎勵
                if InviteConstants.ENABLED:
                    # 邀請人獎勵
                    inviter_reward = InviteConstants.INVITER_REWARD
                    inviter.balance_usdt = (inviter.balance_usdt or Decimal(0)) + inviter_reward
                    inviter.invite_earnings = (inviter.invite_earnings or Decimal(0)) + inviter_reward
                    
                    # 被邀請人獎勵
                    invitee_reward = InviteConstants.INVITEE_REWARD
                    db_user_refreshed.balance_usdt = (db_user_refreshed.balance_usdt or Decimal(0)) + invitee_reward
                    
                    # 記錄交易
                    inviter_tx = Transaction(
                        user_id=inviter.id,
                        type="invite_bonus",
                        currency=CurrencyType.USDT,
                        amount=inviter_reward,
                        balance_before=inviter.balance_usdt - inviter_reward,
                        balance_after=inviter.balance_usdt,
                        note=f"邀請獎勵 - 邀請用戶 {user.id}",
                        status="completed"
                    )
                    invitee_tx = Transaction(
                        user_id=db_user_refreshed.id,
                        type="invite_bonus",
                        currency=CurrencyType.USDT,
                        amount=invitee_reward,
                        balance_before=Decimal(0),
                        balance_after=invitee_reward,
                        note=f"新用戶獎勵 - 由 {inviter.tg_id} 邀請",
                        status="completed"
                    )
                    db.add(inviter_tx)
                    db.add(invitee_tx)
                    
                    # 檢查里程碑獎勵
                    new_invite_count = inviter.invite_count
                    if new_invite_count in InviteConstants.MILESTONES:
                        milestone_reward = InviteConstants.MILESTONES[new_invite_count]
                        inviter.balance_usdt = inviter.balance_usdt + milestone_reward
                        inviter.invite_earnings = inviter.invite_earnings + milestone_reward
                        milestone_tx = Transaction(
                            user_id=inviter.id,
                            type="invite_milestone",
                            currency=CurrencyType.USDT,
                            amount=milestone_reward,
                            balance_before=inviter.balance_usdt - milestone_reward,
                            balance_after=inviter.balance_usdt,
                            note=f"邀請里程碑獎勵 - 達成 {new_invite_count} 人",
                            status="completed"
                        )
                        db.add(milestone_tx)
                        logger.info(f"User {inviter.tg_id} reached invite milestone {new_invite_count}, reward: {milestone_reward}")
                    
                    logger.info(f"Invite rewards: inviter {inviter.tg_id} +{inviter_reward}, invitee {user.id} +{invitee_reward}")
                
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
    
    # 检查用户是否已设置交互模式
    with get_db() as db:
        db_user_refreshed = db.query(User).filter(User.tg_id == user.id).first()
        if not db_user_refreshed:
            logger.error(f"User {user.id} not found after creation")
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 如果是新用户或未设置模式，显示初始设置（语言 + 键盘模式）
        if not db_user_refreshed.interaction_mode or db_user_refreshed.interaction_mode == "auto":
            from bot.handlers.initial_setup import show_initial_setup
            await show_initial_setup(update, context)
            return
        
        # 使用i18n获取欢迎消息（根据用户语言环境）
        from bot.utils.i18n import t
        welcome_text = f"""
🧧 *{t('welcome', user=db_user_refreshed)}*

Hi {user.first_name}！

這裡是最有趣的紅包遊戲平台：
• 💰 發紅包給群友
• 🎁 搶紅包贏大獎
• 📅 每日簽到領積分
• 👥 邀請好友得返佣

快來試試吧！👇
"""
        
        # 获取用户的有效模式
        from bot.utils.mode_helper import get_effective_mode
        from bot.keyboards.unified import get_unified_keyboard
        
        effective_mode = get_effective_mode(db_user_refreshed, update.effective_chat.type)
        chat_type = update.effective_chat.type
        
        # 在 /start 后，同时显示内联按钮和底部键盘，让用户选择
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
        
        # 创建底部键盘（主菜单）
        reply_keyboard = [
            [
                KeyboardButton("💰 錢包"),
                KeyboardButton("🧧 紅包"),
            ],
            [
                KeyboardButton("📈 賺取"),
                KeyboardButton("🎮 遊戲"),
            ],
            [
                KeyboardButton("👤 我的"),
            ],
        ]
        
        # 创建内联按钮（主菜单 + 切换模式）
        inline_keyboard = [
            [
                InlineKeyboardButton("💰 錢包", callback_data="menu:wallet"),
                InlineKeyboardButton("🧧 紅包", callback_data="menu:packets"),
            ],
            [
                InlineKeyboardButton("📈 賺取", callback_data="menu:earn"),
                InlineKeyboardButton("🎮 遊戲", callback_data="menu:game"),
            ],
            [
                InlineKeyboardButton("👤 我的", callback_data="menu:profile"),
            ],
            [
                InlineKeyboardButton("🔄 切換模式", callback_data="switch_mode"),
            ],
        ]
        
        try:
            # 同时发送欢迎消息（带内联按钮）和底部键盘
            result = await update.message.reply_text(
                welcome_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard),
            )
            logger.info(f"✓ Inline keyboard sent successfully to user {user.id}")
            
            # 发送底部键盘
            await update.message.reply_text(
                "💡 您可以使用內聯按鈕或底部鍵盤進行操作：",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
            )
            logger.info(f"✓ Reply keyboard sent successfully to user {user.id}")
        except Exception as e:
            logger.error(f"✗ Error sending keyboard to user {user.id}: {e}", exc_info=True)
            await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def open_miniapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理打開 miniapp 的命令"""
    from shared.config.settings import get_settings
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    
    settings = get_settings()
    command = update.message.text.split()[0].replace("/", "").lower()
    
    # 根據命令映射到對應的 miniapp 頁面
    url_map = {
        "wallet": f"{settings.MINIAPP_URL}/wallet",
        "packets": f"{settings.MINIAPP_URL}/packets",
        "earn": f"{settings.MINIAPP_URL}/earn",
        "game": f"{settings.MINIAPP_URL}/game",
        "profile": f"{settings.MINIAPP_URL}/profile",
    }
    
    url = url_map.get(command, settings.MINIAPP_URL)
    
    keyboard = [[
        InlineKeyboardButton(
            "🚀 打開應用",
            web_app=WebAppInfo(url=url)
        )
    ]]
    
    await update.message.reply_text(
        f"點擊按鈕打開 {command} 頁面：",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    help_text = """
🧧 *Lucky Red 使用指南*

*基本命令：*
/start - 開始使用
/wallet - 打開錢包
/packets - 打開紅包
/earn - 打開賺取
/game - 打開遊戲
/profile - 打開我的
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

