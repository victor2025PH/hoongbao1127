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


class RedPacketType(str, enum.Enum):
    """紅包類型"""
    RANDOM = "random"      # 拼手氣
    EQUAL = "equal"        # 平分
    EXCLUSIVE = "exclusive"  # 專屬


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
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    sent_packets = relationship("RedPacket", back_populates="sender", foreign_keys="RedPacket.sender_id")
    claims = relationship("RedPacketClaim", back_populates="user")
    messages = relationship("Message", back_populates="user")
    notification_settings = relationship("UserNotificationSettings", back_populates="user", uselist=False)
    
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
    
    # 狀態
    status = Column(Enum(RedPacketStatus), default=RedPacketStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 關聯
    claims = relationship("RedPacketClaim", back_populates="red_packet")
    
    __table_args__ = (
        Index("ix_red_packets_status", "status"),
        Index("ix_red_packets_chat_id", "chat_id"),
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
    
    # 時間戳
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_claims_user_packet", "user_id", "red_packet_id"),
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
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_type", "type"),
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

