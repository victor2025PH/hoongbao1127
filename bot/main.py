"""
Lucky Red (搶紅包) - Telegram Bot 主入口
"""
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from loguru import logger
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from shared.config.settings import get_settings
from shared.database.connection import init_db
from bot.handlers import start, redpacket, wallet, checkin, admin, menu, packets, earn, profile, game, keyboard

settings = get_settings()

# 配置日誌
logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


async def setup_commands(app: Application):
    """設置 Bot 命令菜單"""
    commands = [
        BotCommand("start", "開始使用"),
        BotCommand("wallet", "打開錢包"),
        BotCommand("packets", "打開紅包"),
        BotCommand("earn", "打開賺取"),
        BotCommand("game", "打開遊戲"),
        BotCommand("profile", "打開我的"),
        BotCommand("send", "發紅包"),
        BotCommand("checkin", "每日簽到"),
        BotCommand("invite", "邀請好友"),
        BotCommand("help", "幫助說明"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands set up")


async def post_init(app: Application):
    """Bot 初始化後執行"""
    await setup_commands(app)
    
    # 設置 Bot 描述（包含打開應用的說明）
    try:
        if hasattr(app.bot, 'set_my_description'):
            description = f"""🧧 Lucky Red - 搶紅包遊戲平台

💰 發紅包給群友
🎁 搶紅包贏大獎
📅 每日簽到領積分
👥 邀請好友得返佣

點擊下方按鈕或使用菜單打開應用！"""
            await app.bot.set_my_description(description=description)
            logger.info("Bot description set up")
    except Exception as e:
        logger.debug(f"Bot description setup skipped: {e}")
    
    # 設置 Bot 簡短描述（顯示在個人資料頁面）
    try:
        if hasattr(app.bot, 'set_my_short_description'):
            short_description = "🧧 最有趣的紅包遊戲平台 - 發紅包、搶紅包、每日簽到、邀請好友！"
            await app.bot.set_my_short_description(short_description=short_description)
            logger.info("Bot short description set up")
    except Exception as e:
        logger.debug(f"Bot short description setup skipped: {e}")
    
    # 設置菜單按鈕（顯示在輸入框旁邊）- 打開 miniapp
    try:
        if hasattr(app.bot, 'set_chat_menu_button'):
            # 嘗試導入 MenuButtonWebApp
            try:
                from telegram import MenuButtonWebApp, WebAppInfo
                web_app_info = WebAppInfo(url=settings.MINIAPP_URL)
                menu_button = MenuButtonWebApp(text="🎮 打開應用", web_app=web_app_info)
                await app.bot.set_chat_menu_button(menu_button=menu_button)
                logger.info("✅ Bot menu button set up (WebApp) - 聊天欄顯示打開圖標")
            except (ImportError, AttributeError) as e1:
                logger.warning(f"MenuButtonWebApp not available: {e1}")
                # 如果導入失敗，嘗試使用字典方式
                try:
                    await app.bot.set_chat_menu_button(menu_button={
                        "type": "web_app",
                        "text": "🎮 打開應用",
                        "web_app": {
                            "url": settings.MINIAPP_URL
                        }
                    })
                    logger.info("✅ Bot menu button set up (using dict) - 聊天欄顯示打開圖標")
                except Exception as e2:
                    logger.warning(f"Menu button not available: {e2}")
        else:
            # 如果 set_chat_menu_button 不存在，嘗試使用舊的 API
            try:
                from telegram import MenuButtonWebApp, WebAppInfo
                web_app_info = WebAppInfo(url=settings.MINIAPP_URL)
                menu_button = MenuButtonWebApp(text="🎮 打開應用", web_app=web_app_info)
                # 嘗試直接設置（某些版本可能支持）
                await app.bot.set_chat_menu_button(menu_button=menu_button)
                logger.info("✅ Bot menu button set up (fallback) - 聊天欄顯示打開圖標")
            except Exception as e3:
                logger.warning(f"Menu button setup failed: {e3}")
    except Exception as e:
        logger.warning(f"Menu button setup skipped: {e}")
        # 如果設置失敗，不影響 Bot 運行
    
    # 設置描述按鈕（顯示在個人資料頁面）- 這需要在 BotFather 中設置，但我們可以通過描述引導用戶
    # 注意：描述按鈕需要在 BotFather 中手動設置，API 無法直接設置
    # 但我們可以通過設置描述來引導用戶點擊菜單按鈕
    
    logger.info(f"🤖 Bot @{app.bot.username} started!")
    logger.info("📱 聊天欄菜單按鈕已設置（顯示在輸入框旁邊）")
    logger.info("💡 提示：個人資料頁面的描述按鈕需要在 BotFather 中手動設置")


def main():
    """主函數"""
    logger.info(f"🚀 Starting {settings.APP_NAME} Bot")
    
    # 初始化數據庫
    init_db()
    logger.info("✅ Database initialized")
    
    # 創建 Bot 應用
    app = Application.builder().token(settings.BOT_TOKEN).post_init(post_init).build()
    
    # 註冊處理器
    # 命令處理
    app.add_handler(CommandHandler("start", start.start_command))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("wallet", start.open_miniapp_command))
    app.add_handler(CommandHandler("packets", start.open_miniapp_command))
    app.add_handler(CommandHandler("earn", start.open_miniapp_command))
    app.add_handler(CommandHandler("game", start.open_miniapp_command))
    app.add_handler(CommandHandler("profile", start.open_miniapp_command))
    app.add_handler(CommandHandler("send", redpacket.send_command))
    app.add_handler(CommandHandler("checkin", checkin.checkin_command))
    app.add_handler(CommandHandler("invite", start.invite_command))
    
    # 管理員命令
    app.add_handler(CommandHandler("admin", admin.admin_command))
    app.add_handler(CommandHandler("adjust", admin.adjust_command))
    app.add_handler(CommandHandler("broadcast", admin.broadcast_command))
    
    # 回調查詢處理 - 按優先級順序
    # 模式切换 - 必須在其他處理器之前註冊
    from bot.handlers import mode_switch
    app.add_handler(CallbackQueryHandler(mode_switch.switch_mode_callback, pattern=r"^switch_mode$"), group=1)
    app.add_handler(CallbackQueryHandler(mode_switch.set_mode_callback, pattern=r"^set_mode:"), group=1)
    logger.info("[INIT] ✓ Mode switch handlers registered in group=1")
    
    # 添加調試日誌來確認 CallbackQuery 是否被觸發（在模式切換之後，不攔截）
    async def debug_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """調試：記錄所有回調查詢（不處理，只記錄）"""
        if update.callback_query:
            user_id = update.effective_user.id if update.effective_user else None
            callback_data = update.callback_query.data if update.callback_query.data else "[無數據]"
            logger.debug(f"[CALLBACK_DEBUG] Callback received: '{callback_data}' from user {user_id}")
            # 不調用 query.answer()，讓其他處理器處理
            # 不返回任何值，讓處理鏈繼續
    
    # 添加調試處理器（在 group=2，不會攔截模式切換）
    app.add_handler(CallbackQueryHandler(debug_callback_handler, pattern=".*"), group=2)
    logger.debug("[INIT] ✓ debug_callback_handler registered in group=2 (non-blocking)")
    
    # 主菜單
    app.add_handler(CallbackQueryHandler(menu.menu_callback, pattern=r"^menu:"))
    # 初始設置（語言 + 鍵盤模式）
    from bot.handlers import initial_setup
    app.add_handler(CallbackQueryHandler(initial_setup.setup_language_callback, pattern=r"^setup:lang:"), group=1)
    # 語言切換
    from bot.handlers import language
    app.add_handler(CallbackQueryHandler(language.language_callback, pattern=r"^language:"))
    # 錢包
    app.add_handler(CallbackQueryHandler(wallet.wallet_callback, pattern=r"^wallet:"))
    # 紅包
    app.add_handler(CallbackQueryHandler(redpacket.claim_callback, pattern=r"^claim:"))
    # 先注册更具体的模式（packets:send:*），再注册通用的模式（packets:*）
    app.add_handler(CallbackQueryHandler(packets.send_packet_menu_callback, pattern=r"^packets:send"))
    app.add_handler(CallbackQueryHandler(packets.packets_callback, pattern=r"^packets:"))
    # 賺取
    app.add_handler(CallbackQueryHandler(checkin.checkin_callback, pattern=r"^checkin:"))
    app.add_handler(CallbackQueryHandler(earn.earn_callback, pattern=r"^earn:"))
    # 遊戲
    app.add_handler(CallbackQueryHandler(game.game_callback, pattern=r"^game:"))
    # 個人資料
    app.add_handler(CallbackQueryHandler(profile.profile_callback, pattern=r"^profile:"))
    
    # 文本消息處理
    # 優先處理回覆鍵盤按鈕
    from bot.handlers import keyboard
    
    # 添加一個捕獲所有消息的調試處理器（放在最前面，用於診斷）
    async def catch_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """捕獲所有消息用於調試"""
        try:
            if update.message:
                user_id = update.effective_user.id if update.effective_user else None
                msg_text = update.message.text if update.message.text else "[非文本消息]"
                logger.warning(f"[CATCH_ALL] Message received: '{msg_text}' from user {user_id}")
                print(f"[CATCH_ALL] Message received: '{msg_text}' from user {user_id}", flush=True)
        except Exception as e:
            logger.error(f"[CATCH_ALL] Error: {e}", exc_info=True)
            print(f"[CATCH_ALL] Error: {e}", flush=True)
        # 不阻止其他處理器處理（不返回，讓其他處理器繼續處理）
    
    # 添加調試日誌來確認 MessageHandler 是否被觸發
    async def debug_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """調試：記錄所有文本消息"""
        try:
            if update.message and update.message.text:
                user_id = update.effective_user.id if update.effective_user else None
                # 使用 logger.warning 確保日誌一定會輸出（即使 LOG_LEVEL=INFO）
                logger.warning(f"[DEBUG] Text message received: '{update.message.text}' from user {user_id}")
                print(f"[DEBUG] Text message received: '{update.message.text}' from user {user_id}", flush=True)
            # 繼續處理
            await keyboard.handle_reply_keyboard(update, context)
        except Exception as e:
            logger.error(f"[DEBUG] Error in debug_text_handler: {e}", exc_info=True)
            print(f"[DEBUG] Error in debug_text_handler: {e}", flush=True)
            # 嘗試發送錯誤消息給用戶
            try:
                if update.message:
                    from bot.keyboards.reply_keyboards import get_main_reply_keyboard
                    await update.message.reply_text(
                        "處理消息時發生錯誤，請稍後再試或使用 /start 重新開始",
                        reply_markup=get_main_reply_keyboard()
                    )
            except:
                pass
    
    # 註冊 MessageHandler - 必須在 CommandHandler 之後
    # 注意：python-telegram-bot 的處理器按 group 和註冊順序執行
    # group 越小越先執行，同一 group 內按註冊順序
    
    # 先註冊 catch_all_handler（group=0，用於調試，會先執行）
    try:
        app.add_handler(MessageHandler(filters.ALL, catch_all_handler), group=0)
        logger.warning("[INIT] ✓ catch_all_handler registered in group=0")
        print("[INIT] ✓ catch_all_handler registered in group=0", flush=True)
    except (AttributeError, TypeError) as e:
        # 如果 filters.ALL 不存在，嘗試使用 None
        try:
            app.add_handler(MessageHandler(None, catch_all_handler), group=0)
            logger.warning("[INIT] ✓ catch_all_handler registered (using None filter) in group=0")
            print("[INIT] ✓ catch_all_handler registered (using None filter) in group=0", flush=True)
        except Exception as e2:
            logger.error(f"[INIT] ✗ Failed to register catch_all_handler: {e2}", exc_info=True)
            print(f"[INIT] ✗ Failed to register catch_all_handler: {e2}", flush=True)
    
    # 然後註冊文本消息處理器（group=1，在 CommandHandler 之後）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, debug_text_handler), group=1)
    logger.warning("[INIT] ✓ MessageHandler for reply keyboard registered in group=1")
    print("[INIT] ✓ MessageHandler for reply keyboard registered in group=1", flush=True)
    
    # 記錄所有已註冊的處理器
    try:
        total_handlers = len(app.handlers.get(0, [])) + len(app.handlers.get(1, []))
        logger.warning(f"[INIT] Total handlers registered: group0={len(app.handlers.get(0, []))}, group1={len(app.handlers.get(1, []))}, total={total_handlers}")
        print(f"[INIT] Total handlers: group0={len(app.handlers.get(0, []))}, group1={len(app.handlers.get(1, []))}", flush=True)
    except Exception as e:
        logger.error(f"[INIT] Error counting handlers: {e}", exc_info=True)
    # 然後處理用戶輸入的群組 ID/鏈接和祝福語（如果不在等待輸入狀態，會被回覆鍵盤處理器處理）
    
    # 添加錯誤處理
    async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE):
        """處理所有未捕獲的錯誤"""
        error = context.error
        error_name = type(error).__name__
        error_msg = str(error)
        
        # 嘗試導入錯誤類（不同版本可能有不同的類名）
        try:
            from telegram.error import Conflict
            is_conflict = isinstance(error, Conflict)
        except (ImportError, AttributeError):
            is_conflict = False
        
        # 處理特定錯誤
        if is_conflict or "Conflict" in error_name or "terminated by other getUpdates" in error_msg:
            logger.error("Bot conflict detected! Another instance may be running.")
            logger.error("Please stop all other Bot instances and restart.")
            # 不退出，讓它繼續嘗試（可能會自動恢復）
        elif "Unauthorized" in error_name or "Unauthorized" in error_msg or "invalid token" in error_msg.lower():
            logger.error("Bot token is invalid or unauthorized!")
        elif "Network" in error_name or "Connection" in error_msg or "TimedOut" in error_name:
            logger.warning("Network error, will retry...")
        else:
            update_info = f"Update {update.update_id}" if update and hasattr(update, 'update_id') else "No update"
            logger.error(f"Exception while handling {update_info}: {error}", exc_info=error)
    
    # 註冊錯誤處理器
    app.add_error_handler(error_handler)
    
    # 啟動 Bot
    logger.info("🤖 Bot is running...")
    logger.warning("=" * 50)
    logger.warning("Bot 正在啟動，準備接收消息...")
    logger.warning("=" * 50)
    print("=" * 50, flush=True)
    print("Bot 正在啟動，準備接收消息...", flush=True)
    print("=" * 50, flush=True)
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # 啟動時丟棄待處理的更新，避免衝突
            close_loop=False
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
