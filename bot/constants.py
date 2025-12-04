"""
Lucky Red - 常量定義
統一管理所有常量
"""
from decimal import Decimal


class PacketConstants:
    """紅包相關常量"""
    MAX_COUNT = 100  # 每個紅包最多份數
    MIN_AMOUNT = Decimal("0.01")  # 最小金額
    DEFAULT_MESSAGE = "恭喜發財！🧧"  # 默認祝福語
    BOMB_COUNTS = [5, 10]  # 紅包炸彈允許的數量（雙雷5，單雷10）
    BOMB_NUMBER_MIN = 0  # 炸彈數字最小值
    BOMB_NUMBER_MAX = 9  # 炸彈數字最大值
    MESSAGE_MAX_LENGTH = 256  # 祝福語最大長度
    EXPIRY_HOURS = 24  # 紅包過期時間（小時）


class WalletConstants:
    """錢包相關常量"""
    MIN_DEPOSIT_USDT = Decimal("10.0")  # USDT 最小充值金額
    MIN_DEPOSIT_TON = Decimal("10.0")  # TON 最小充值金額
    MIN_WITHDRAW_USDT = Decimal("10.0")  # USDT 最小提現金額
    MIN_WITHDRAW_TON = Decimal("10.0")  # TON 最小提現金額


class CheckinConstants:
    """簽到相關常量"""
    REWARDS = {
        1: 10,   # 第1天
        2: 20,   # 第2天
        3: 30,   # 第3天
        4: 40,   # 第4天
        5: 50,   # 第5天
        6: 60,   # 第6天
        7: 100,  # 第7天（獎勵加倍）
    }
    DEFAULT_REWARD = 10  # 默認獎勵


class TaskConstants:
    """任務相關常量"""
    # 每日任務獎勵
    DAILY_CHECKIN_REWARD = 20  # 每日簽到獎勵
    DAILY_CLAIM_REWARD = 10  # 搶紅包獎勵（每個）
    DAILY_SEND_REWARD = 15  # 發紅包獎勵（每個）
    
    # 成就任務獎勵
    ACHIEVEMENT_FIRST_DEPOSIT = 100  # 首次充值獎勵
    ACHIEVEMENT_INVITE_MASTER = 200  # 邀請達人獎勵（10人）
    ACHIEVEMENT_PACKET_MASTER = 500  # 紅包大師獎勵（100個）
    
    # 成就任務目標
    INVITE_MASTER_TARGET = 10  # 邀請達人目標人數
    PACKET_MASTER_TARGET = 100  # 紅包大師目標數量


class InviteConstants:
    """邀請獎勵相關常量"""
    # 邀請獎勵 (USDT)
    INVITER_REWARD = Decimal("1.0")  # 邀請人獎勵
    INVITEE_REWARD = Decimal("0.5")  # 被邀請人獎勵
    
    # 多級返佣比例
    LEVEL1_COMMISSION = Decimal("0.05")  # 一級返佣 5%
    LEVEL2_COMMISSION = Decimal("0.02")  # 二級返佣 2%
    
    # 邀請里程碑獎勵
    MILESTONES = {
        5: Decimal("5.0"),    # 邀請 5 人獎勵
        10: Decimal("15.0"),  # 邀請 10 人獎勵
        25: Decimal("50.0"),  # 邀請 25 人獎勵
        50: Decimal("150.0"), # 邀請 50 人獎勵
        100: Decimal("500.0"), # 邀請 100 人獎勵
    }
    
    # 邀請活動開關
    ENABLED = True  # 是否啟用邀請獎勵


class CacheConstants:
    """緩存相關常量"""
    USER_CACHE_TTL = 300  # 用戶緩存 TTL（秒，5分鐘）
    DEFAULT_CACHE_TTL = 300  # 默認緩存 TTL（秒）


class APIConstants:
    """API 相關常量"""
    REQUEST_TIMEOUT = 10.0  # 請求超時時間（秒）
    MAX_RETRIES = 3  # 最大重試次數


class ValidationConstants:
    """驗證相關常量"""
    MIN_USERNAME_LENGTH = 1
    MAX_USERNAME_LENGTH = 64
    MIN_MESSAGE_LENGTH = 0
    MAX_MESSAGE_LENGTH = 256
    CHAT_ID_MIN = -10**18  # 群組 ID 最小值（理論值）
    CHAT_ID_MAX = 10**18  # 群組 ID 最大值（理論值）
