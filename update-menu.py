"""
更新 Bot 菜單按鈕和命令
"""
import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Bot, BotCommand
from shared.config.settings import get_settings

async def update_menu():
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # 更新命令
        commands = [
            BotCommand('start', '開始使用'),
            BotCommand('wallet', '我的錢包'),
            BotCommand('send', '發紅包'),
            BotCommand('checkin', '每日簽到'),
            BotCommand('invite', '邀請好友'),
            BotCommand('help', '幫助說明'),
        ]
        await bot.set_my_commands(commands)
        print('✓ Commands updated successfully')
        
        # 嘗試設置菜單按鈕
        try:
            from telegram import MenuButtonCommands
            menu_button = MenuButtonCommands()
            await bot.set_chat_menu_button(menu_button=menu_button)
            print('✓ Menu button updated successfully')
        except (ImportError, AttributeError) as e:
            print(f'⚠ MenuButtonCommands not available: {e}')
            # 嘗試使用字典格式
            try:
                await bot.set_chat_menu_button(menu_button={'type': 'commands'})
                print('✓ Menu button updated (using dict format)')
            except Exception as e2:
                print(f'⚠ Could not set menu button: {e2}')
                print('  Commands are still available via / command')
        
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(update_menu())
