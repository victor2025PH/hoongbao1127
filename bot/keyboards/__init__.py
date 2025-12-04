"""
Lucky Red - 鍵盤生成器
統一管理所有機器人按鈕和菜單
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from shared.config.settings import get_settings

settings = get_settings()


def get_main_menu(user=None):
    """主菜單 - 對應 miniapp 底部導航，所有按鈕在機器人中完成"""
    from bot.utils.i18n import t
    
    keyboard = [
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
            InlineKeyboardButton(t("language", user=user), callback_data="menu:language"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_wallet_menu():
    """錢包子菜單 - 所有按鈕打開 miniapp"""
    keyboard = [
        [
            InlineKeyboardButton("💵 充值", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/recharge")),
            InlineKeyboardButton("💸 提現", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/withdraw")),
        ],
        [
            InlineKeyboardButton("📜 交易記錄", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/wallet?tab=records")),
            InlineKeyboardButton("🔄 兌換", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange")),
        ],
        [
            InlineKeyboardButton("◀️ 返回主菜單", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}")),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_packets_menu(user=None):
    """紅包子菜單 - 所有按鈕在機器人中完成"""
    from bot.utils.i18n import t
    
    keyboard = [
        [
            InlineKeyboardButton(t("view_packets", user=user), callback_data="packets:list"),
            InlineKeyboardButton(t("send_packet", user=user), callback_data="packets:send"),
        ],
        [
            InlineKeyboardButton(t("my_packets", user=user), callback_data="packets:my"),
        ],
        [
            InlineKeyboardButton(t("return_main", user=user), callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_earn_menu():
    """賺取子菜單 - 所有按鈕打開 miniapp"""
    keyboard = [
        [
            InlineKeyboardButton("📅 每日簽到", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/earn?tab=checkin")),
            InlineKeyboardButton("👥 邀請好友", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/earn?tab=invite")),
        ],
        [
            InlineKeyboardButton("🎯 任務中心", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/earn?tab=tasks")),
            InlineKeyboardButton("🎰 幸運轉盤", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/lucky-wheel")),
        ],
        [
            InlineKeyboardButton("◀️ 返回主菜單", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}")),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_menu():
    """個人資料子菜單 - 所有按鈕打開 miniapp"""
    keyboard = [
        [
            InlineKeyboardButton("📊 我的資料", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/profile")),
            InlineKeyboardButton("📈 統計數據", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/profile?tab=stats")),
        ],
        [
            InlineKeyboardButton("⚙️ 設置", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/profile?tab=settings")),
        ],
        [
            InlineKeyboardButton("◀️ 返回主菜單", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}")),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_exchange_menu():
    """兌換子菜單 - 所有按鈕打開 miniapp"""
    keyboard = [
        [
            InlineKeyboardButton("USDT → TON", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=usdt&to=ton")),
            InlineKeyboardButton("TON → USDT", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=ton&to=usdt")),
        ],
        [
            InlineKeyboardButton("USDT → 能量", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=usdt&to=points")),
            InlineKeyboardButton("能量 → USDT", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=points&to=usdt")),
        ],
        [
            InlineKeyboardButton("TON → 能量", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=ton&to=points")),
            InlineKeyboardButton("能量 → TON", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/exchange?from=points&to=ton")),
        ],
        [
            InlineKeyboardButton("◀️ 返回錢包", web_app=WebAppInfo(url=f"{settings.MINIAPP_URL}/wallet")),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_wallet():
    """返回錢包菜單"""
    keyboard = [
        [InlineKeyboardButton("◀️ 返回錢包", callback_data="menu:wallet")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main():
    """返回主菜單"""
    keyboard = [
        [InlineKeyboardButton("◀️ 返回主菜單", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_currency_selection(action_prefix: str):
    """貨幣選擇按鈕（用於充值/提現）"""
    keyboard = [
        [
            InlineKeyboardButton("USDT", callback_data=f"{action_prefix}:usdt"),
            InlineKeyboardButton("TON", callback_data=f"{action_prefix}:ton"),
        ],
        [
            InlineKeyboardButton("◀️ 返回", callback_data="menu:wallet"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_cancel(confirm_data: str, cancel_data: str = "menu:main"):
    """確認/取消按鈕"""
    keyboard = [
        [
            InlineKeyboardButton("✅ 確認", callback_data=confirm_data),
            InlineKeyboardButton("❌ 取消", callback_data=cancel_data),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
