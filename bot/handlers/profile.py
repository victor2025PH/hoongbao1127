"""
Lucky Red - 個人資料處理器
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from loguru import logger

from shared.config.settings import get_settings
from shared.database.connection import get_db
from shared.database.models import User
from bot.keyboards import get_profile_menu, get_back_to_main

settings = get_settings()


async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理個人資料回調"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    
    # 獲取用戶（帶緩存）
    from bot.utils.user_helpers import get_user_from_update
    db_user = await get_user_from_update(update, context)
    if not db_user:
        await query.message.reply_text("請先使用 /start 註冊")
        return
    
    if action == "info":
        await show_profile_info(query, db_user)
    elif action == "stats":
        await show_profile_stats(query, db_user)
    elif action == "settings":
        await show_profile_settings(query, db_user)


async def show_profile_info(query, db_user):
    """顯示個人資料"""
    # 在會話內重新查詢用戶以確保數據最新
    from shared.database.connection import get_db
    from shared.database.models import User
    
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await query.edit_message_text("發生錯誤，請稍後再試")
            return
        
        username = user.username or '未設置'
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        tg_id = user.tg_id
        level = user.level
        xp = user.xp or 0
        created_at = user.created_at.strftime('%Y-%m-%d') if user.created_at else '未知'
        balance_usdt = float(user.balance_usdt or 0)
        balance_ton = float(user.balance_ton or 0)
        balance_points = user.balance_points or 0
    
    text = f"""
👤 *我的資料*

*基本信息：*
• 用戶名：@{username}
• 姓名：{first_name} {last_name}
• 用戶ID：`{tg_id}`

*賬戶信息：*
• 等級：Lv.{level}
• 經驗：{xp} XP
• 註冊時間：{created_at}

*餘額：*
• USDT: `{balance_usdt:.4f}`
• TON: `{balance_ton:.4f}`
• 能量: `{balance_points}`
"""
    
    keyboard = [
        [
            InlineKeyboardButton("◀️ 返回", callback_data="menu:profile"),
        ],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_profile_stats(query, db_user):
    """顯示統計數據"""
    # 在會話內重新查詢用戶以確保數據最新
    from shared.database.connection import get_db
    from shared.database.models import User, RedPacket, RedPacketClaim
    from sqlalchemy import func
    
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == db_user.tg_id).first()
        if not user:
            await query.edit_message_text("發生錯誤，請稍後再試")
            return
        
        # 使用关系查询统计（在会话内）
        sent_count = db.query(RedPacket).filter(RedPacket.sender_id == user.id).count()
        claimed_count = db.query(RedPacketClaim).filter(RedPacketClaim.user_id == user.id).count()
        
        # 计算总发送和总领取金额
        total_sent_result = db.query(func.sum(RedPacket.total_amount)).filter(RedPacket.sender_id == user.id).scalar()
        total_sent = float(total_sent_result or 0)
        
        total_claimed_result = db.query(func.sum(RedPacketClaim.amount)).filter(RedPacketClaim.user_id == user.id).scalar()
        total_claimed = float(total_claimed_result or 0)
        
        invite_count = user.invite_count or 0
        invite_earnings = float(user.invite_earnings or 0)
        consecutive_days = user.checkin_streak or 0  # 使用 checkin_streak 代替 consecutive_checkin_days
        
        # 计算总签到次数（如果有签到记录表，否则使用 checkin_streak）
        total_checkin = user.checkin_streak or 0
    
    text = f"""
📈 *統計數據*

*紅包統計：*
• 已發紅包：{sent_count} 個
• 已搶紅包：{claimed_count} 個
• 總發送金額：{total_sent:.2f} USDT
• 總搶到金額：{total_claimed:.2f} USDT

*邀請統計：*
• 邀請人數：{invite_count} 人
• 邀請收益：{invite_earnings:.4f} USDT

*簽到統計：*
• 連續簽到：{consecutive_days} 天
• 總簽到次數：{total_checkin} 次

💡 提示：更多詳細統計請在 miniapp 中查看
"""
    
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 打開 miniapp 查看詳情",
                web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/profile")
            ),
        ],
        [
            InlineKeyboardButton("◀️ 返回", callback_data="menu:profile"),
        ],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_profile_settings(query, db_user):
    """顯示設置"""
    text = """
⚙️ *設置*

*賬戶設置：*
• 通知設置
• 語言設置
• 隱私設置

💡 提示：完整的設置功能請在 miniapp 中使用
"""
    
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 打開 miniapp 設置",
                web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/profile")
            ),
        ],
        [
            InlineKeyboardButton("◀️ 返回", callback_data="menu:profile"),
        ],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
