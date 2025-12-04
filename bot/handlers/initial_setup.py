"""
Lucky Red - 初始设置处理器
处理新用户的语言和键盘模式选择
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from shared.database.connection import get_db
from shared.database.models import User
from bot.utils.i18n import t, update_user_language, get_user_language
from bot.utils.mode_helper import update_user_mode, get_mode_name, get_mode_description
from bot.keyboards.unified import get_unified_keyboard


async def show_initial_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示初始设置界面（语言 + 键盘模式）"""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    # 获取用户当前语言（如果有）
    with get_db() as db:
        db_user = db.query(User).filter(User.tg_id == user.id).first()
        if not db_user:
            await update.message.reply_text("發生錯誤，請稍後再試")
            return
        
        current_lang = get_user_language(user=db_user)
    
    text = f"""
🧧 *歡迎來到 Lucky Red！*

Hi {user.first_name}！

請先選擇您的語言，然後選擇您喜歡的交互方式：

*🌐 語言選擇*
請選擇界面語言：

*⌨️ 交互方式*
• ⌨️ 底部鍵盤 - 傳統 bot 體驗，在群組中也能使用
• 🔘 內聯按鈕 - 流暢交互，點擊消息中的按鈕
• 📱 MiniApp - 最豐富的功能，最佳體驗（僅私聊）
• 🔄 自動 - 根據上下文自動選擇最佳模式

💡 您可以隨時在主菜單中切換語言和模式
"""
    
    # 如果在群组中，提示 MiniApp 不可用
    if chat_type in ["group", "supergroup"]:
        text += "\n⚠️ 注意：MiniApp 模式在群組中不可用"
    
    keyboard = get_initial_setup_keyboard(current_lang)
    
    try:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error sending initial setup: {e}", exc_info=True)


def get_initial_setup_keyboard(current_lang: str = "zh-TW"):
    """获取初始设置键盘（语言选择）"""
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if current_lang == 'zh-TW' else ''} 繁體中文",
                callback_data="setup:lang:zh-TW"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if current_lang == 'zh-CN' else ''} 简体中文",
                callback_data="setup:lang:zh-CN"
            ),
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if current_lang == 'en' else ''} English",
                callback_data="setup:lang:en"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(keyboard)


async def setup_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理语言选择回调"""
    query = update.callback_query
    if not query:
        return
    
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[SETUP] User {user_id} selecting language, callback_data: {query.data}")
    
    try:
        await query.answer("正在設置語言...")
    except Exception as e:
        logger.error(f"Error answering query: {e}")
    
    # 解析语言代码
    if not query.data or not query.data.startswith("setup:lang:"):
        logger.error(f"Invalid callback_data: {query.data}")
        return
    
    lang_code = query.data.split(":")[2]
    
    # 更新用户语言
    success = await update_user_language(user_id, lang_code)
    
    if not success:
        await query.message.reply_text("❌ 設置語言失敗，請稍後再試")
        return
    
    # 重新获取用户以获取新语言
    with get_db() as db:
        user = db.query(User).filter(User.tg_id == user_id).first()
        if not user:
            await query.message.reply_text("發生錯誤，請稍後再試")
            return
        
        # 显示键盘模式选择
        await show_mode_selection_after_lang(query, user, update.effective_chat.type)


async def show_mode_selection_after_lang(query, db_user, chat_type: str):
    """在语言选择后显示键盘模式选择"""
    lang_names = {
        "zh-TW": "繁體中文",
        "zh-CN": "简体中文",
        "en": "English",
    }
    current_lang = get_user_language(user=db_user)
    lang_name = lang_names.get(current_lang, "繁體中文")
    
    # 使用i18n获取文本
    text = f"""
✅ *{t('lang_changed', user=db_user, lang=lang_name)}*

{t('select_operation', user=db_user)}

*⌨️ {t('mode_keyboard', user=db_user)}* - 傳統 bot 體驗，在群組中也能使用
*🔘 {t('mode_inline', user=db_user)}* - 流暢交互，點擊消息中的按鈕
*📱 {t('mode_miniapp', user=db_user)}* - 最豐富的功能，最佳體驗（僅私聊）
*🔄 {t('mode_auto', user=db_user)}* - 根據上下文自動選擇最佳模式

💡 您可以隨時在主菜單中切換模式
"""
    
    # 如果在群组中，提示 MiniApp 不可用
    if chat_type in ["group", "supergroup"]:
        text += "\n⚠️ 注意：MiniApp 模式在群組中不可用"
    
    keyboard = get_mode_selection_keyboard()
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)
        try:
            await query.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e2:
            logger.error(f"Error sending new message: {e2}", exc_info=True)


def get_mode_selection_keyboard():
    """获取键盘模式选择键盘"""
    from bot.keyboards.unified import get_mode_selection_keyboard as get_unified_mode_keyboard
    keyboard = get_unified_mode_keyboard()
    return keyboard
