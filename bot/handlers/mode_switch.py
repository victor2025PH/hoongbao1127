"""
Lucky Red - 模式切换处理器
"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from bot.utils.mode_helper import (
    get_effective_mode, 
    update_user_mode, 
    get_mode_name,
    get_mode_description
)
from bot.utils.user_helpers import get_user_from_update
from bot.keyboards.unified import get_unified_keyboard, get_mode_selection_keyboard


async def switch_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理模式切换回调 - 显示三种模式选择菜单"""
    query = update.callback_query
    if not query:
        return
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering query: {e}")
    
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    # 获取用户
    user = await get_user_from_update(update, context)
    if not user:
        await query.message.reply_text("請先使用 /start 註冊")
        return
    
    # 显示模式选择界面（三种模式：内联按钮、底部键盘、MiniApp）
    await show_mode_selection_from_keyboard(update, context, user)


async def set_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理设置模式回调（首次设置）"""
    query = update.callback_query
    if not query:
        logger.error("set_mode_callback called but no callback_query")
        return
    
    user_id = update.effective_user.id if update.effective_user else None
    logger.info(f"[SET_MODE] User {user_id} selecting mode, callback_data: {query.data}")
    
    try:
        await query.answer("正在設置模式...")
    except Exception as e:
        logger.error(f"Error answering query: {e}")
    
    # 解析模式
    if not query.data or not query.data.startswith("set_mode:"):
        logger.error(f"Invalid callback_data: {query.data}")
        return
    
    mode = query.data.split(":")[1]
    chat_type = update.effective_chat.type
    
    logger.info(f"[SET_MODE] User {user_id} selected mode: {mode}, chat_type: {chat_type}")
    
    # 检查模式是否可用
    if mode == "miniapp" and chat_type in ["group", "supergroup"]:
        await query.message.reply_text(
            "⚠️ MiniApp 模式在群組中不可用，已自動切換到內聯按鈕模式。"
        )
        mode = "inline"
    
    # 更新用户偏好
    logger.info(f"[SET_MODE] Updating user {user_id} mode to {mode}")
    success = await update_user_mode(user_id, mode, update_last=True)
    
    if not success:
        logger.error(f"[SET_MODE] Failed to update user {user_id} mode")
        try:
            await query.message.reply_text(
                "❌ 設置模式失敗，請稍後再試\n\n"
                "如果問題持續，請聯繫管理員。"
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
        return
    
    logger.info(f"[SET_MODE] Successfully updated user {user_id} mode to {mode}")
    
    # 获取模式名称和描述
    mode_name = get_mode_name(mode)
    mode_desc = get_mode_description(mode)
    
    # 更新消息
    try:
        keyboard = get_unified_keyboard(mode, "main", chat_type)
        
        # 根据键盘类型处理
        from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup
        
        if isinstance(keyboard, ReplyKeyboardMarkup):
            # 底部键盘模式：先编辑消息显示确认（不带键盘），然后发送新消息带键盘
            try:
                await query.edit_message_text(
                    f"✅ 已設置為 {mode_name}\n\n"
                    f"💡 {mode_desc}\n\n"
                    f"請使用底部鍵盤進行操作。\n"
                    f"您可以隨時在主菜單中切換模式。"
                )
            except Exception as edit_e:
                logger.warning(f"Could not edit message: {edit_e}, sending new message")
            
            # 发送新消息带回复键盘（不能编辑消息添加 ReplyKeyboardMarkup）
            await query.message.reply_text(
                "⌨️ 請使用底部鍵盤進行操作：",
                reply_markup=keyboard
            )
            logger.info(f"[SET_MODE] Sent ReplyKeyboardMarkup for user {user_id}")
            
        elif isinstance(keyboard, InlineKeyboardMarkup):
            # 内联按钮模式：直接编辑消息
            await query.edit_message_text(
                f"✅ 已設置為 {mode_name}\n\n"
                f"💡 {mode_desc}\n\n"
                f"您可以隨時在主菜單中切換模式。",
                reply_markup=keyboard
            )
            logger.info(f"[SET_MODE] Updated message with InlineKeyboardMarkup for user {user_id}")
        else:
            # 其他情况：尝试编辑消息
            await query.edit_message_text(
                f"✅ 已設置為 {mode_name}\n\n"
                f"💡 {mode_desc}",
                reply_markup=keyboard
            )
        
        logger.info(f"[SET_MODE] Successfully updated message for user {user_id}")
    except Exception as e:
        logger.error(f"Error updating message: {e}", exc_info=True)
        try:
            # 如果编辑失败，发送新消息
            keyboard = get_unified_keyboard(mode, "main", chat_type)
            from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup
            
            if isinstance(keyboard, ReplyKeyboardMarkup):
                await query.message.reply_text(
                    f"✅ 已設置為 {mode_name}\n\n"
                    f"💡 {mode_desc}\n\n"
                    f"⌨️ 請使用底部鍵盤進行操作：",
                    reply_markup=keyboard
                )
            else:
                await query.message.reply_text(
                    f"✅ 已設置為 {mode_name}\n\n"
                    f"💡 {mode_desc}",
                    reply_markup=keyboard
                )
        except Exception as e2:
            logger.error(f"Error sending fallback message: {e2}", exc_info=True)
            await query.message.reply_text(f"✅ 已設置為 {mode_name}")


async def show_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示模式选择界面（首次使用）"""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    text = f"""
🧧 *歡迎來到 Lucky Red！*

Hi {user.first_name}！

請選擇您喜歡的交互方式：

*⌨️ 底部鍵盤* - 傳統 bot 體驗，在群組中也能使用
*🔘 內聯按鈕* - 流暢交互，點擊消息中的按鈕
*📱 MiniApp* - 最豐富的功能，最佳體驗（僅私聊）
*🔄 自動* - 根據上下文自動選擇最佳模式

💡 您可以隨時使用「🔄 切換模式」按鈕切換
"""
    
    # 如果在群组中，提示 MiniApp 不可用
    if chat_type in ["group", "supergroup"]:
        text += "\n⚠️ 注意：MiniApp 模式在群組中不可用"
    
    try:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_mode_selection_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending mode selection: {e}", exc_info=True)


async def show_mode_selection_from_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, db_user):
    """从键盘模式显示模式选择界面（三种模式：内联按钮、底部键盘、MiniApp）"""
    chat_type = update.effective_chat.type
    
    # 获取用户语言
    from bot.utils.i18n import t, get_user_language
    current_lang = get_user_language(user=db_user)
    
    text = f"""
🔄 *{t('switch_mode', user=db_user)}*

{t('select_operation', user=db_user)}

*{t('mode_inline', user=db_user)}* - 流暢交互，點擊消息中的按鈕
*{t('mode_keyboard', user=db_user)}* - 傳統 bot 體驗，在群組中也能使用
*{t('mode_miniapp', user=db_user)}* - 最豐富的功能，最佳體驗（僅私聊）

💡 選擇您喜歡的交互方式：
"""
    
    # 如果在群组中，提示 MiniApp 不可用
    if chat_type in ["group", "supergroup"]:
        text += "\n⚠️ 注意：MiniApp 模式在群組中不可用，將自動切換到內聯按鈕模式"
    
    # 创建三种模式选择键盘（只显示三种主要模式，不包括auto）- 按钮中包含图标
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton(f"🔘 {t('mode_inline', user=db_user)}", callback_data="set_mode:inline"),
        ],
        [
            InlineKeyboardButton(f"⌨️ {t('mode_keyboard', user=db_user)}", callback_data="set_mode:keyboard"),
        ],
        [
            InlineKeyboardButton(f"📱 {t('mode_miniapp', user=db_user)}", callback_data="set_mode:miniapp"),
        ],
    ]
    
    try:
        # 如果是 callback_query，编辑消息；否则发送新消息
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Error sending mode selection from keyboard: {e}", exc_info=True)
        # 如果编辑失败，尝试发送新消息
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e2:
            logger.error(f"Error sending fallback message: {e2}", exc_info=True)
