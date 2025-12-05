"""
Lucky Red (搶紅包) - 數據庫模型
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, Numeric, ForeignKey, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class CurrencyType(str, enum.Enum):
    """貨幣類型"""
    USDT = "usdt"
    TON = "ton"
    STARS = "stars"
    POINTS = "points"


class CurrencySource(str, enum.Enum):
    """資金來源類型 - 用於流動性管理"""
    REAL_CRYPTO = "real_crypto"      # 真實加密貨幣充值
    STARS_CREDIT = "stars_credit"    # Telegram Stars 兌換
    BONUS = "bonus"                  # 獎勵/活動
    REFERRAL = "referral"            # 推薦獎勵


class WithdrawableStatus(str, enum.Enum):
    """可提現狀態"""
    LOCKED = "locked"                # 鎖定中
    COOLDOWN = "cooldown"            # 冷卻期
    WITHDRAWABLE = "withdrawable"    # 可提現


class RiskLevel(str, enum.Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedPacketType(str, enum.Enum):
    """紅包類型"""
    RANDOM = "random"      # 拼手氣
    EQUAL = "equal"        # 平分
    EXCLUSIVE = "exclusive"  # 專屬


class RedPacketVisibility(str, enum.Enum):
    """紅包可見性"""
    PRIVATE = "private"    # 私密紅包（發送到指定群組或用戶）
    PUBLIC = "public"      # 公開紅包（用戶發送的公開紅包）
    TASK = "task"          # 任務紅包
    REWARD = "reward"      # 獎勵紅包
    SYSTEM = "system"      # 系統紅包


class RedPacketSource(str, enum.Enum):
    """紅包來源"""
    USER_PUBLIC = "user_public"      # 用戶發送的公開紅包
    USER_PRIVATE = "user_private"    # 用戶發送的私密紅包
    TASK = "task"                    # 任務紅包
    REWARD = "reward"                # 獎勵紅包
    SYSTEM = "system"                # 系統紅包


class RedPacketStatus(str, enum.Enum):
    """紅包狀態"""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class User(Base):
    """用戶表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    language_code = Column(String(10), default="zh-TW")
    
    # 錢包餘額
    balance_usdt = Column(Numeric(20, 8), default=0)
    balance_ton = Column(Numeric(20, 8), default=0)
    balance_stars = Column(BigInteger, default=0)
    balance_points = Column(BigInteger, default=0)
    
    # 等級和經驗
    level = Column(Integer, default=1)
    xp = Column(BigInteger, default=0)
    
    # 邀請
    invited_by = Column(BigInteger, nullable=True)
    invite_code = Column(String(16), unique=True, nullable=True)
    invite_count = Column(Integer, default=0)
    invite_earnings = Column(Numeric(20, 8), default=0)
    
    # 簽到
    last_checkin = Column(DateTime, nullable=True)
    checkin_streak = Column(Integer, default=0)
    
    # 狀態
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # 交互模式偏好
    interaction_mode = Column(String(20), default="auto")  # "keyboard", "inline", "miniapp", "auto"
    last_interaction_mode = Column(String(20), default="keyboard")  # 上次使用的模式
    seamless_switch_enabled = Column(Boolean, default=True)  # 是否启用无缝切换
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    sent_packets = relationship("RedPacket", back_populates="sender", foreign_keys="RedPacket.sender_id")
    claims = relationship("RedPacketClaim", back_populates="user")
    messages = relationship("Message", back_populates="user")
    notification_settings = relationship("UserNotificationSettings", back_populates="user", uselist=False)
    task_completions = relationship("TaskCompletion", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_users_invite_code", "invite_code"),
    )


class RedPacket(Base):
    """紅包表"""
    __tablename__ = "red_packets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    
    # 發送者
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender = relationship("User", back_populates="sent_packets", foreign_keys=[sender_id])
    
    # 目標群組
    chat_id = Column(BigInteger, nullable=True)  # 索引在 __table_args__ 中定義
    chat_title = Column(String(256), nullable=True)
    message_id = Column(BigInteger, nullable=True)
    
    # 紅包信息
    currency = Column(Enum(CurrencyType), default=CurrencyType.USDT)
    packet_type = Column(Enum(RedPacketType), default=RedPacketType.RANDOM)
    total_amount = Column(Numeric(20, 8), nullable=False)
    total_count = Column(Integer, nullable=False)
    claimed_amount = Column(Numeric(20, 8), default=0)
    claimed_count = Column(Integer, default=0)
    
    # 祝福語
    message = Column(String(256), default="恭喜發財！🧧")
    
    # 紅包炸彈相關（僅當 packet_type = EQUAL 時使用）
    bomb_number = Column(Integer, nullable=True)  # 炸彈數字（0-9），用於紅包炸彈遊戲
    
    # 狀態
    status = Column(Enum(RedPacketStatus), default=RedPacketStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=True)
    
    # 任務紅包相關字段
    visibility = Column(Enum(RedPacketVisibility), default=RedPacketVisibility.PRIVATE)  # 可見性
    source_type = Column(Enum(RedPacketSource), default=RedPacketSource.USER_PRIVATE)  # 來源類型
    task_type = Column(String(50), nullable=True)  # 任務類型：checkin, invite, share, claim, send等
    task_requirement = Column(JSON, nullable=True)  # 任務要求（JSON格式）
    task_completed_users = Column(JSON, default=list)  # 已完成任務的用戶ID列表
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # 軟刪除時間戳
    
    # 關聯
    claims = relationship("RedPacketClaim", back_populates="red_packet")
    task_completions = relationship("TaskCompletion", back_populates="red_packet", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_red_packets_status", "status"),
        Index("ix_red_packets_chat_id", "chat_id"),
        Index("ix_red_packets_status_created", "status", "created_at"),
        Index("ix_red_packets_sender_created", "sender_id", "created_at"),
        Index("ix_red_packets_chat_status", "chat_id", "status"),
        Index("ix_red_packets_expires_at", "expires_at"),
    )


class RedPacketClaim(Base):
    """紅包領取記錄"""
    __tablename__ = "red_packet_claims"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 關聯
    red_packet_id = Column(Integer, ForeignKey("red_packets.id"), nullable=False)
    red_packet = relationship("RedPacket", back_populates="claims")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="claims")
    
    # 領取金額
    amount = Column(Numeric(20, 8), nullable=False)
    is_luckiest = Column(Boolean, default=False)  # 手氣最佳
    
    # 紅包炸彈相關
    is_bomb = Column(Boolean, default=False)  # 是否踩雷
    penalty_amount = Column(Numeric(20, 8), nullable=True)  # 賠付金額（如果踩雷）
    
    # 時間戳
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_claims_user_packet", "user_id", "red_packet_id"),
        Index("ix_claims_user_created", "user_id", "claimed_at"),
        Index("ix_claims_packet_created", "red_packet_id", "claimed_at"),
    )


class TaskCompletion(Base):
    """任務完成記錄"""
    __tablename__ = "task_completions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 關聯
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="task_completions")
    red_packet_id = Column(Integer, ForeignKey("red_packets.id"), nullable=False)
    red_packet = relationship("RedPacket", back_populates="task_completions")
    
    # 任務信息
    task_type = Column(String(50), nullable=False)  # checkin, invite, share, claim, send等
    completed_at = Column(DateTime, default=datetime.utcnow)  # 任務完成時間
    claimed_at = Column(DateTime, nullable=True)  # 領取紅包的時間
    reward_amount = Column(Numeric(20, 8), nullable=True)  # 實際領取的金額
    
    __table_args__ = (
        Index("ix_task_completions_user_id", "user_id"),
        Index("ix_task_completions_red_packet_id", "red_packet_id"),
        Index("ix_task_completions_task_type", "task_type"),
        Index("ix_task_completions_user_task", "user_id", "task_type"),
    )


class DailyTask(Base):
    """每日任務配置"""
    __tablename__ = "daily_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), unique=True, nullable=False)  # checkin, invite, share等
    task_name = Column(String(100), nullable=False)  # 任務名稱
    task_description = Column(String(500), nullable=False)  # 任務描述
    requirement = Column(JSON, nullable=False)  # 任務要求（JSON格式）
    reward_amount = Column(Numeric(20, 8), nullable=False)  # 獎勵金額
    reward_currency = Column(Enum(CurrencyType), default=CurrencyType.USDT)
    is_active = Column(Boolean, default=True)  # 是否啟用
    sort_order = Column(Integer, default=0)  # 排序
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_daily_tasks_task_type", "task_type"),
        Index("ix_daily_tasks_is_active", "is_active"),
    )


class Transaction(Base):
    """交易記錄"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 交易類型
    type = Column(String(32), nullable=False)  # deposit, withdraw, send, receive, checkin, invite
    currency = Column(Enum(CurrencyType), default=CurrencyType.USDT)
    amount = Column(Numeric(20, 8), nullable=False)
    
    # 餘額快照
    balance_before = Column(Numeric(20, 8), nullable=True)
    balance_after = Column(Numeric(20, 8), nullable=True)
    
    # 關聯 ID
    ref_id = Column(String(64), nullable=True)  # 紅包ID、訂單ID等
    
    # 備註
    note = Column(Text, nullable=True)
    
    # 狀態（用於充值/提現審核）
    status = Column(String(16), default="completed")  # pending, completed, rejected, cancelled
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_type", "type"),
        Index("ix_transactions_status", "status"),
    )


class CheckinRecord(Base):
    """簽到記錄"""
    __tablename__ = "checkin_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    checkin_date = Column(DateTime, nullable=False)
    day_of_streak = Column(Integer, default=1)
    reward_points = Column(BigInteger, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_checkin_user_date", "user_id", "checkin_date"),
    )


class MessageType(str, enum.Enum):
    """消息類型"""
    SYSTEM = "system"          # 系統消息
    MINIAPP = "miniapp"        # Miniapp 內部消息
    TELEGRAM = "telegram"      # Telegram Bot 消息
    BOT = "bot"                # 機器人自動消息
    REDPACKET = "redpacket"    # 紅包相關
    BALANCE = "balance"        # 餘額變動
    ACTIVITY = "activity"     # 活動通知


class MessageStatus(str, enum.Enum):
    """消息狀態"""
    UNREAD = "unread"
    READ = "read"
    DELETED = "deleted"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_type = Column(Enum(MessageType), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.UNREAD)
    
    title = Column(String(256), nullable=True)
    content = Column(Text, nullable=False)
    action_url = Column(String(512), nullable=True)  # 點擊後跳轉的鏈接
    
    # 來源信息
    source = Column(String(64), nullable=True)  # 來源標識（bot_id, system, etc.）
    source_name = Column(String(128), nullable=True)  # 來源名稱
    
    # 回復相關
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    can_reply = Column(Boolean, default=False)
    
    # 元數據（使用 meta_data 避免與 SQLAlchemy 的 metadata 衝突）
    meta_data = Column(JSON, nullable=True)  # 存儲額外數據（如紅包ID、金額等）
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # 關聯
    user = relationship("User", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])
    
    __table_args__ = (
        Index("ix_messages_user_status", "user_id", "status"),
        Index("ix_messages_type", "message_type"),
    )


class UserNotificationSettings(Base):
    """用戶通知設置表"""
    __tablename__ = "user_notification_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # 提示方式設置
    notification_method = Column(String(32), default="both")  # "miniapp_only", "both", "telegram_only", "off"
    
    # 各類型消息的開關
    enable_system = Column(Boolean, default=True)
    enable_redpacket = Column(Boolean, default=True)
    enable_balance = Column(Boolean, default=True)
    enable_activity = Column(Boolean, default=True)
    enable_miniapp = Column(Boolean, default=True)
    enable_telegram = Column(Boolean, default=True)
    
    # 更新時間
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="notification_settings")


# ==================== 管理后台新增表 ====================

class AdminUser(Base):
    """管理員用戶表"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(128), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    role = relationship("Role", back_populates="admin_users")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=True)  # 權限列表 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    admin_users = relationship("AdminUser", back_populates="role")


class AdminLog(Base):
    """管理員操作日志表"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    action_type = Column(String(64), nullable=False)  # create, update, delete, etc.
    resource_type = Column(String(64), nullable=False)  # user, red_packet, etc.
    resource_id = Column(String(64), nullable=True)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_admin_logs_admin_id", "admin_id"),
        Index("ix_admin_logs_resource", "resource_type", "resource_id"),
    )


class SystemConfig(Base):
    """系統配置表"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TelegramGroup(Base):
    """Telegram 群組表"""
    __tablename__ = "telegram_groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=True)
    type = Column(String(32), nullable=True)  # group, supergroup, channel
    username = Column(String(128), nullable=True, index=True)
    member_count = Column(Integer, nullable=True)
    bot_status = Column(String(32), nullable=True)  # member, administrator, creator, left, kicked
    invite_link = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_tg_groups_chat_id", "chat_id"),
        Index("ix_tg_groups_username", "username"),
    )


class TelegramMessage(Base):
    """Telegram 消息記錄表"""
    __tablename__ = "telegram_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=True)  # Telegram 消息 ID
    chat_id = Column(BigInteger, nullable=False, index=True)  # 群組/用戶 ID
    chat_type = Column(String(32), nullable=True)  # group, supergroup, private
    from_user_id = Column(BigInteger, nullable=True)  # 發送者 Telegram ID
    to_user_id = Column(BigInteger, nullable=True, index=True)  # 接收者 Telegram ID
    message_type = Column(String(32), nullable=True)  # text, photo, video, document, etc.
    content = Column(Text, nullable=True)
    media_url = Column(String(512), nullable=True)
    keyboard = Column(JSON, nullable=True)  # 鍵盤按鈕 JSON
    status = Column(String(32), default="sent")  # sent, failed, pending
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_tg_msgs_chat_id", "chat_id"),
        Index("ix_tg_msgs_to_user", "to_user_id"),
        Index("ix_tg_msgs_created", "created_at"),
    )


class MessageTemplate(Base):
    """消息模板表"""
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=True)  # notification, marketing, system, etc.
    content = Column(Text, nullable=False)  # 模板內容，支持變量
    variables = Column(JSON, nullable=True)  # 可用變量列表
    message_type = Column(String(32), default="text")  # text, photo, video, etc.
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AutomationTask(Base):
    """自動化任務表"""
    __tablename__ = "automation_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    task_type = Column(String(32), nullable=False)  # scheduled, triggered
    trigger_config = Column(JSON, nullable=True)  # 觸發配置（Cron 表達式、事件等）
    action_config = Column(JSON, nullable=True)  # 執行動作配置
    is_enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_automation_tasks_enabled", "is_enabled"),
        Index("ix_automation_tasks_next_run", "next_run_at"),
    )


class Report(Base):
    """報表表"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(64), nullable=False)  # user, transaction, red_packet, etc.
    name = Column(String(128), nullable=False)
    config = Column(JSON, nullable=True)  # 報表配置
    file_path = Column(String(512), nullable=True)
    file_format = Column(String(16), nullable=True)  # xlsx, csv, pdf, json
    status = Column(String(32), default="pending")  # pending, generating, completed, failed
    generated_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_reports_status", "status"),
        Index("ix_reports_type", "report_type"),
    )


# ==================== 安全與合規層相關表 ====================

class LedgerCategory(str, enum.Enum):
    """帳本分類"""
    DEPOSIT = "deposit"              # 充值
    WITHDRAW = "withdraw"            # 提現
    SEND_PACKET = "send_packet"      # 發送紅包
    CLAIM_PACKET = "claim_packet"    # 領取紅包
    REFUND = "refund"                # 退款
    STARS_CONVERSION = "stars_conversion"  # Stars 兌換
    FIAT_DEPOSIT = "fiat_deposit"    # 法幣充值
    REFERRAL_BONUS = "referral_bonus"  # 推薦獎勵
    GAME_WIN = "game_win"            # 遊戲獲勝
    GAME_LOSS = "game_loss"          # 遊戲輸錢
    FEE = "fee"                      # 手續費


class LedgerEntry(Base):
    """
    帳本條目表 - 複式記帳系統
    用於追蹤所有資金流動，包含資金來源和可提現狀態
    """
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    
    # 用戶關聯
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 交易信息
    currency = Column(Enum(CurrencyType), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)  # 正數=貸記，負數=借記
    balance_after = Column(Numeric(20, 8), nullable=False)  # 交易後餘額快照
    category = Column(Enum(LedgerCategory), nullable=False)
    
    # 資金來源追蹤 - 流動性管理
    currency_source = Column(Enum(CurrencySource), default=CurrencySource.REAL_CRYPTO)
    withdrawable_status = Column(Enum(WithdrawableStatus), default=WithdrawableStatus.WITHDRAWABLE)
    cooldown_until = Column(DateTime, nullable=True)  # 冷卻期結束時間
    
    # 遊戲流水要求
    turnover_required = Column(Numeric(20, 8), default=0)  # 需要的流水
    turnover_completed = Column(Numeric(20, 8), default=0)  # 已完成流水
    
    # 關聯引用
    ref_type = Column(String(32), nullable=True)  # red_packet, transaction, etc.
    ref_id = Column(String(64), nullable=True)
    
    # 配對交易（複式記帳的另一端）
    paired_entry_id = Column(Integer, ForeignKey("ledger_entries.id"), nullable=True)
    
    # 備註和元數據
    note = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_ledger_user_currency", "user_id", "currency"),
        Index("ix_ledger_user_created", "user_id", "created_at"),
        Index("ix_ledger_category", "category"),
        Index("ix_ledger_ref", "ref_type", "ref_id"),
        Index("ix_ledger_source_status", "currency_source", "withdrawable_status"),
        Index("ix_ledger_cooldown", "cooldown_until"),
    )


class MagicLinkToken(Base):
    """
    Magic Link 令牌表
    用於無密碼登入 H5/Web 版本
    """
    __tablename__ = "magic_link_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tg_id = Column(BigInteger, nullable=False, index=True)  # Telegram 用戶 ID
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    # 安全性
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    # 狀態
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_magic_link_token", "token"),
        Index("ix_magic_link_tg_id", "tg_id"),
        Index("ix_magic_link_expires", "expires_at"),
    )


class DeviceFingerprint(Base):
    """
    設備指紋表
    用於反 Sybil 攻擊檢測
    """
    __tablename__ = "device_fingerprints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fingerprint_id = Column(String(64), nullable=False, index=True)
    
    # 設備信息
    device_info = Column(JSON, nullable=True)  # 設備類型、操作系統等
    browser_info = Column(JSON, nullable=True)  # 瀏覽器信息
    
    # 風險評估
    confidence_score = Column(Numeric(5, 4), nullable=True)  # 0-1
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    
    # 追蹤
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    request_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index("ix_fingerprint_id", "fingerprint_id"),
        Index("ix_fingerprint_user", "user_id"),
        Index("ix_fingerprint_risk", "risk_level"),
    )


class IPSession(Base):
    """
    IP 會話追蹤表
    用於檢測同一 IP 的多會話攻擊
    """
    __tablename__ = "ip_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 會話信息
    session_id = Column(String(64), nullable=True)
    session_start = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # 活動統計
    packet_claims = Column(Integer, default=0)
    suspicious_actions = Column(Integer, default=0)
    
    # 地理信息
    country_code = Column(String(2), nullable=True)
    city = Column(String(128), nullable=True)
    
    __table_args__ = (
        Index("ix_ip_session_ip", "ip_address"),
        Index("ix_ip_session_user", "user_id"),
        Index("ix_ip_session_active", "is_active"),
        Index("ix_ip_session_activity", "last_activity"),
    )


class SybilAlert(Base):
    """
    Sybil 攻擊警報表
    記錄所有被阻止的可疑行為
    """
    __tablename__ = "sybil_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 關聯信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(64), nullable=True)
    fingerprint_id = Column(String(64), nullable=True)
    
    # 警報類型
    alert_type = Column(String(32), nullable=False)  # new_account, ip_limit, rate_limit, fingerprint
    alert_code = Column(String(64), nullable=False)
    
    # 詳情
    message = Column(Text, nullable=True)
    request_path = Column(String(256), nullable=True)
    request_method = Column(String(16), nullable=True)
    meta_data = Column(JSON, nullable=True)  # 包含完整請求信息
    
    # 處理狀態
    is_reviewed = Column(Boolean, default=False)
    reviewed_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    action_taken = Column(String(64), nullable=True)  # blocked, warned, banned, false_positive
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_sybil_alert_type", "alert_type"),
        Index("ix_sybil_alert_user", "user_id"),
        Index("ix_sybil_alert_ip", "ip_address"),
        Index("ix_sybil_alert_reviewed", "is_reviewed"),
    )


class UserBalance(Base):
    """
    用戶餘額表 - 快取層
    按資金來源分類的餘額匯總
    """
    __tablename__ = "user_balances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyType), nullable=False)
    
    # 總餘額
    total_balance = Column(Numeric(20, 8), default=0)
    
    # 按來源分類的餘額
    balance_real_crypto = Column(Numeric(20, 8), default=0)  # 真實加密貨幣
    balance_stars_credit = Column(Numeric(20, 8), default=0)  # Stars 兌換
    balance_bonus = Column(Numeric(20, 8), default=0)  # 獎勵
    balance_referral = Column(Numeric(20, 8), default=0)  # 推薦
    
    # 可提現餘額
    withdrawable_balance = Column(Numeric(20, 8), default=0)
    locked_balance = Column(Numeric(20, 8), default=0)  # 冷卻中
    
    # 流水統計
    total_turnover = Column(Numeric(20, 8), default=0)  # 總流水
    pending_turnover = Column(Numeric(20, 8), default=0)  # 待完成流水
    
    # 更新時間
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_user_balance_user_currency", "user_id", "currency", unique=True),
    )

