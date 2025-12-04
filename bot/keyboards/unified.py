"""
Lucky Red - 统一键盘生成器
支持三种交互模式：底部键盘、内联按钮、MiniApp
"""
from telegram import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup, 
    KeyboardButton, InlineKeyboardButton, WebAppInfo
)
from shared.config.settings import get_settings

settings = get_settings()


# 菜单定义
MENU_DEFINITIONS = {
    "main": [
        ("💰 錢包", "wallet", f"{settings.MINIAPP_URL}/wallet"),
        ("🧧 紅包", "packets", f"{settings.MINIAPP_URL}/packets"),
        ("📈 賺取", "earn", f"{settings.MINIAPP_URL}/earn"),
        ("🎮 遊戲", "game", f"{settings.MINIAPP_URL}/game"),
        ("👤 我的", "profile", f"{settings.MINIAPP_URL}/profile"),
    ],
    "wallet": [
        ("💵 充值", "recharge", f"{settings.MINIAPP_URL}/recharge"),
        ("💸 提現", "withdraw", f"{settings.MINIAPP_URL}/withdraw"),
        ("📜 交易記錄", "records", f"{settings.MINIAPP_URL}/wallet?tab=records"),
        ("🔄 兌換", "exchange", f"{settings.MINIAPP_URL}/exchange"),
        ("◀️ 返回主菜單", "main", f"{settings.MINIAPP_URL}"),
    ],
    "packets": [
        ("📋 查看紅包", "list", f"{settings.MINIAPP_URL}/packets"),
        ("➕ 發紅包", "send", f"{settings.MINIAPP_URL}/send-red-packet"),
        ("🎁 我的紅包", "my", f"{settings.MINIAPP_URL}/packets?tab=my"),
        ("◀️ 返回主菜單", "main", f"{settings.MINIAPP_URL}"),
    ],
    "earn": [
        ("📅 每日簽到", "checkin", f"{settings.MINIAPP_URL}/earn?tab=checkin"),
        ("👥 邀請好友", "invite", f"{settings.MINIAPP_URL}/earn?tab=invite"),
        ("🎯 任務中心", "tasks", f"{settings.MINIAPP_URL}/earn?tab=tasks"),
        ("🎰 幸運轉盤", "wheel", f"{settings.MINIAPP_URL}/lucky-wheel"),
        ("◀️ 返回主菜單", "main", f"{settings.MINIAPP_URL}"),
    ],
    "game": [
        ("🎰 金運局", "gold", f"{settings.MINIAPP_URL}/game"),
        ("🎡 幸運轉盤", "wheel", f"{settings.MINIAPP_URL}/lucky-wheel"),
        ("◀️ 返回主菜單", "main", f"{settings.MINIAPP_URL}"),
    ],
    "profile": [
        ("📊 我的資料", "info", f"{settings.MINIAPP_URL}/profile"),
        ("📈 統計數據", "stats", f"{settings.MINIAPP_URL}/profile?tab=stats"),
        ("⚙️ 設置", "settings", f"{settings.MINIAPP_URL}/profile?tab=settings"),
        ("◀️ 返回主菜單", "main", f"{settings.MINIAPP_URL}"),
    ],
}


def get_mode_indicator(mode: str) -> str:
    """获取模式指示器文本"""
    indicators = {
        "keyboard": "⌨️ 键盘模式",
        "inline": "🔘 内联模式",
        "miniapp": "📱 MiniApp模式",
        "auto": "🔄 自动模式"
    }
    return indicators.get(mode, "⌨️ 键盘模式")


def get_unified_keyboard(
    mode: str, 
    menu_type: str = "main", 
    chat_type: str = "private"
):
    """
    统一键盘生成器
    
    Args:
        mode: 交互模式 ("keyboard", "inline", "miniapp", "auto")
        menu_type: 菜单类型 ("main", "wallet", "packets", etc.)
        chat_type: 聊天类型 ("private", "group", "supergroup")
    
    Returns:
        根据模式返回不同的键盘对象
    """
    # 如果是 auto 模式，根据聊天类型智能选择
    if mode == "auto":
        if chat_type in ["group", "supergroup"]:
            mode = "inline"  # 群组中使用内联按钮
        else:
            mode = "keyboard"  # 私聊中默认使用键盘
    
    # 如果 miniapp 模式在群组中，回退到 inline
    if mode == "miniapp" and chat_type in ["group", "supergroup"]:
        mode = "inline"
    
    # 获取菜单项
    items = MENU_DEFINITIONS.get(menu_type, MENU_DEFINITIONS["main"])
    
    if mode == "keyboard":
        # 底部键盘模式：使用普通文本按钮
        keyboard = []
        for i in range(0, len(items), 2):
            row = [KeyboardButton(items[i][0])]
            if i + 1 < len(items):
                row.append(KeyboardButton(items[i+1][0]))
            keyboard.append(row)
        
        # 不添加切换按钮到底部键盘（避免重复，切换模式通过内联按钮实现）
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    elif mode == "inline":
        # 内联按钮模式：使用 callback_data
        keyboard = []
        for i in range(0, len(items), 2):
            row = [
                InlineKeyboardButton(
                    items[i][0], 
                    callback_data=f"menu:{items[i][1]}"
                )
            ]
            if i + 1 < len(items):
                row.append(
                    InlineKeyboardButton(
                        items[i+1][0], 
                        callback_data=f"menu:{items[i+1][1]}"
                    )
                )
            keyboard.append(row)
        
        # 添加切换按钮
        keyboard.append([
            InlineKeyboardButton("🔄 切換模式", callback_data="switch_mode")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    elif mode == "miniapp":
        # MiniApp 模式：使用 web_app
        keyboard = []
        for i in range(0, len(items), 2):
            row = [
                KeyboardButton(
                    items[i][0], 
                    web_app=WebAppInfo(url=items[i][2])
                )
            ]
            if i + 1 < len(items):
                row.append(
                    KeyboardButton(
                        items[i+1][0], 
                        web_app=WebAppInfo(url=items[i+1][2])
                    )
                )
            keyboard.append(row)
        
        # 添加切换按钮（使用内联按钮，因为 web_app 按钮不能切换模式）
        inline_keyboard = [
            [InlineKeyboardButton("🔄 切換模式", callback_data="switch_mode")]
        ]
        
        return {
            "reply": ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            "inline": InlineKeyboardMarkup(inline_keyboard)
        }
    
    # 默认返回键盘模式
    return get_unified_keyboard("keyboard", menu_type, chat_type)


def get_mode_selection_keyboard():
    """获取模式选择键盘（用于首次设置）"""
    keyboard = [
        [
            InlineKeyboardButton("⌨️ 底部键盘", callback_data="set_mode:keyboard"),
            InlineKeyboardButton("🔘 内联按钮", callback_data="set_mode:inline"),
        ],
        [
            InlineKeyboardButton("📱 MiniApp", callback_data="set_mode:miniapp"),
            InlineKeyboardButton("🔄 自动", callback_data="set_mode:auto"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
