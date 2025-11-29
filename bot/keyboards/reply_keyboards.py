"""
Lucky Red - 回覆鍵盤（Reply Keyboard）
對應 miniapp 的所有功能，支持多級菜單
"""
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, WebAppInfo
from shared.config.settings import get_settings

settings = get_settings()


def get_main_reply_keyboard():
    """主回覆鍵盤 - 一級菜單（對應 miniapp 底部導航）"""
    keyboard = [
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
            KeyboardButton("📱 打開應用"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇功能或輸入命令..."
    )


def get_wallet_reply_keyboard():
    """錢包回覆鍵盤 - 二級菜單"""
    keyboard = [
        [
            KeyboardButton("💵 充值"),
            KeyboardButton("💸 提現"),
        ],
        [
            KeyboardButton("📜 交易記錄"),
            KeyboardButton("🔄 兌換"),
        ],
        [
            KeyboardButton("◀️ 返回主菜單"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇錢包操作..."
    )


def get_packets_reply_keyboard():
    """紅包回覆鍵盤 - 二級菜單"""
    keyboard = [
        [
            KeyboardButton("📋 查看紅包"),
            KeyboardButton("➕ 發紅包"),
        ],
        [
            KeyboardButton("🎁 我的紅包"),
        ],
        [
            KeyboardButton("◀️ 返回主菜單"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇紅包操作..."
    )


def get_send_packet_currency_keyboard():
    """發紅包 - 選擇幣種（三級菜單）"""
    keyboard = [
        [
            KeyboardButton("💵 發 USDT 紅包"),
            KeyboardButton("💵 發 TON 紅包"),
        ],
        [
            KeyboardButton("⚡ 發能量紅包"),
        ],
        [
            KeyboardButton("◀️ 返回紅包"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇紅包幣種..."
    )


def get_send_packet_type_keyboard():
    """發紅包 - 選擇類型（四級菜單）"""
    keyboard = [
        [
            KeyboardButton("🎲 手氣最佳"),
            KeyboardButton("💣 紅包炸彈"),
        ],
        [
            KeyboardButton("◀️ 返回幣種"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇紅包類型..."
    )


def get_send_packet_amount_keyboard(currency: str, packet_type: str):
    """發紅包 - 選擇金額（五級菜單）"""
    # 根據幣種顯示不同的金額選項
    if currency.lower() == "usdt":
        amounts = ["10", "50", "100", "200", "500"]
    elif currency.lower() == "ton":
        amounts = ["10", "50", "100", "200", "500"]
    else:  # points
        amounts = ["100", "500", "1000", "2000", "5000"]
    
    keyboard = []
    # 每行兩個按鈕
    for i in range(0, len(amounts), 2):
        row = [KeyboardButton(f"💰 {amounts[i]}")]
        if i + 1 < len(amounts):
            row.append(KeyboardButton(f"💰 {amounts[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([KeyboardButton("📝 自定義金額")])
    keyboard.append([KeyboardButton("◀️ 返回類型")])
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇或輸入金額..."
    )


def get_send_packet_count_keyboard(currency: str, packet_type: str, amount: str):
    """發紅包 - 選擇數量（六級菜單）"""
    # 紅包炸彈只能選擇 5 或 10
    if packet_type == "equal":
        counts = ["5", "10"]
        keyboard = [
            [
                KeyboardButton("5 份（雙雷）"),
                KeyboardButton("10 份（單雷）"),
            ],
            [
                KeyboardButton("◀️ 返回金額"),
            ],
        ]
    else:
        # 手氣最佳可以選擇更多數量
        counts = ["5", "10", "20", "50", "100"]
        keyboard = []
        for i in range(0, len(counts), 2):
            row = [KeyboardButton(f"📦 {counts[i]} 份")]
            if i + 1 < len(counts):
                row.append(KeyboardButton(f"📦 {counts[i+1]} 份"))
            keyboard.append(row)
        keyboard.append([KeyboardButton("📝 自定義數量")])
        keyboard.append([KeyboardButton("◀️ 返回金額")])
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇或輸入數量..."
    )


def get_send_packet_group_keyboard():
    """發紅包 - 選擇群組（七級菜單）"""
    keyboard = [
        [
            KeyboardButton("🔍 查找群組"),
            KeyboardButton("📝 輸入群組 ID"),
        ],
        [
            KeyboardButton("📌 綁定群組"),
        ],
        [
            KeyboardButton("◀️ 返回數量"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="輸入群組 ID 或鏈接..."
    )


def get_send_packet_confirm_keyboard():
    """發紅包 - 確認發送（八級菜單）"""
    keyboard = [
        [
            KeyboardButton("✅ 確認發送"),
            KeyboardButton("❌ 取消"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="確認發送紅包..."
    )


def get_earn_reply_keyboard():
    """賺取回覆鍵盤 - 二級菜單"""
    keyboard = [
        [
            KeyboardButton("📅 每日簽到"),
            KeyboardButton("👥 邀請好友"),
        ],
        [
            KeyboardButton("🎯 任務中心"),
            KeyboardButton("🎰 幸運轉盤"),
        ],
        [
            KeyboardButton("◀️ 返回主菜單"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇賺取方式..."
    )


def get_game_reply_keyboard():
    """遊戲回覆鍵盤 - 二級菜單"""
    keyboard = [
        [
            KeyboardButton("🎰 金運局"),
            KeyboardButton("🎡 幸運轉盤"),
        ],
        [
            KeyboardButton("◀️ 返回主菜單"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇遊戲..."
    )


def get_profile_reply_keyboard():
    """個人資料回覆鍵盤 - 二級菜單"""
    keyboard = [
        [
            KeyboardButton("📊 我的資料"),
            KeyboardButton("📈 統計數據"),
        ],
        [
            KeyboardButton("⚙️ 設置"),
        ],
        [
            KeyboardButton("◀️ 返回主菜單"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇查看內容..."
    )


def get_exchange_reply_keyboard():
    """兌換回覆鍵盤 - 三級菜單"""
    keyboard = [
        [
            KeyboardButton("USDT → TON"),
            KeyboardButton("TON → USDT"),
        ],
        [
            KeyboardButton("USDT → 能量"),
            KeyboardButton("能量 → USDT"),
        ],
        [
            KeyboardButton("TON → 能量"),
            KeyboardButton("能量 → TON"),
        ],
        [
            KeyboardButton("◀️ 返回錢包"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇兌換類型..."
    )


def get_deposit_reply_keyboard():
    """充值回覆鍵盤 - 三級菜單"""
    keyboard = [
        [
            KeyboardButton("💵 充值 USDT"),
            KeyboardButton("💵 充值 TON"),
        ],
        [
            KeyboardButton("◀️ 返回錢包"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇充值幣種..."
    )


def get_withdraw_reply_keyboard():
    """提現回覆鍵盤 - 三級菜單"""
    keyboard = [
        [
            KeyboardButton("💸 提現 USDT"),
            KeyboardButton("💸 提現 TON"),
        ],
        [
            KeyboardButton("◀️ 返回錢包"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="選擇提現幣種..."
    )


def remove_reply_keyboard():
    """移除回覆鍵盤"""
    return ReplyKeyboardRemove()


def get_webapp_button(text: str, url: str):
    """創建 Web App 按鈕"""
    return KeyboardButton(text, web_app=WebAppInfo(url=url))
