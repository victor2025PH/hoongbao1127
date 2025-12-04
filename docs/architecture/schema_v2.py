"""
Global Social-Fi Platform - Database Schema V2
Supports: Universal Access + Off-Chain Ledger + Fiat Gateway
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, Numeric, ForeignKey, Enum, Index, JSON,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

Base = declarative_base()


# ============================================================
# ENUMS
# ============================================================

class AuthProvider(str, enum.Enum):
    """Authentication Provider"""
    TELEGRAM = "telegram"
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"
    PHONE = "phone"
    WALLET = "wallet"  # Web3 wallet (MetaMask, etc.)
    PARTICLE = "particle"  # Particle Network
    WEB3AUTH = "web3auth"


class CurrencyType(str, enum.Enum):
    """Currency Types"""
    USDT = "usdt"
    TON = "ton"
    STARS = "stars"
    POINTS = "points"
    CNY = "cny"  # Fiat: Chinese Yuan
    USD = "usd"  # Fiat: US Dollar


class LedgerEntryType(str, enum.Enum):
    """Ledger Entry Types (Double-Entry)"""
    CREDIT = "credit"  # 貸方 (增加)
    DEBIT = "debit"    # 借方 (減少)


class LedgerCategory(str, enum.Enum):
    """Ledger Categories"""
    # Red Packet
    PACKET_SEND = "packet_send"
    PACKET_CLAIM = "packet_claim"
    PACKET_REFUND = "packet_refund"
    
    # Transfers
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    
    # Fiat
    FIAT_DEPOSIT = "fiat_deposit"
    FIAT_WITHDRAWAL = "fiat_withdrawal"
    
    # Crypto
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    
    # Swap
    SWAP_FROM = "swap_from"
    SWAP_TO = "swap_to"
    
    # Rewards
    CHECKIN_REWARD = "checkin_reward"
    REFERRAL_BONUS = "referral_bonus"
    GAME_REWARD = "game_reward"
    
    # Fees
    PLATFORM_FEE = "platform_fee"
    WITHDRAWAL_FEE = "withdrawal_fee"


class PaymentProvider(str, enum.Enum):
    """Payment Providers"""
    ALCHEMY_PAY = "alchemy_pay"
    UNLIMIT = "unlimit"
    STRIPE = "stripe"
    UNIONPAY = "unionpay"
    WECHAT = "wechat"
    ALIPAY = "alipay"


class PaymentStatus(str, enum.Enum):
    """Payment Status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class IdentityStatus(str, enum.Enum):
    """Identity Verification Status"""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


# ============================================================
# CORE TABLES - Universal Identity
# ============================================================

class User(Base):
    """
    Unified User Entity
    Supports hybrid identities: Telegram, Social Login, Web3 Wallet
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # ===== Primary Identity (at least one required) =====
    # Telegram
    tg_id = Column(BigInteger, unique=True, nullable=True, index=True)
    tg_username = Column(String(64), nullable=True, index=True)
    tg_first_name = Column(String(64), nullable=True)
    tg_last_name = Column(String(64), nullable=True)
    tg_photo_url = Column(String(512), nullable=True)
    
    # Email/Phone (Social Login)
    email = Column(String(256), unique=True, nullable=True, index=True)
    email_verified = Column(Boolean, default=False)
    phone = Column(String(32), unique=True, nullable=True, index=True)
    phone_verified = Column(Boolean, default=False)
    
    # Web3 Wallet
    wallet_address = Column(String(64), unique=True, nullable=True, index=True)
    wallet_chain = Column(String(32), nullable=True)  # ethereum, ton, solana, etc.
    
    # ===== Profile =====
    display_name = Column(String(128), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    language_code = Column(String(10), default="zh-TW")
    timezone = Column(String(64), default="Asia/Shanghai")
    
    # ===== KYC / Identity =====
    identity_status = Column(Enum(IdentityStatus), default=IdentityStatus.UNVERIFIED)
    kyc_level = Column(Integer, default=0)  # 0: None, 1: Basic, 2: Advanced
    country_code = Column(String(3), nullable=True)  # ISO 3166-1 alpha-2
    
    # ===== Level & XP =====
    level = Column(Integer, default=1)
    xp = Column(BigInteger, default=0)
    
    # ===== Referral =====
    invite_code = Column(String(16), unique=True, nullable=True, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invite_count = Column(Integer, default=0)
    total_referral_earnings = Column(Numeric(20, 8), default=0)
    
    # ===== Preferences =====
    interaction_mode = Column(String(20), default="auto")
    notification_enabled = Column(Boolean, default=True)
    
    # ===== Status =====
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    
    # ===== Timestamps =====
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ===== Relationships =====
    auth_providers = relationship("UserAuthProvider", back_populates="user")
    balances = relationship("UserBalance", back_populates="user")
    ledger_entries = relationship("LedgerEntry", back_populates="user")
    sent_packets = relationship("RedPacket", back_populates="sender", foreign_keys="RedPacket.sender_id")
    
    __table_args__ = (
        Index("ix_users_uuid", "uuid"),
        Index("ix_users_email_verified", "email", "email_verified"),
        Index("ix_users_wallet", "wallet_address", "wallet_chain"),
        # At least one identity required
        CheckConstraint(
            "(tg_id IS NOT NULL) OR (email IS NOT NULL) OR (wallet_address IS NOT NULL)",
            name="ck_users_identity_required"
        ),
    )


class UserAuthProvider(Base):
    """
    Linked Authentication Providers
    One user can link multiple auth methods
    """
    __tablename__ = "user_auth_providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    provider = Column(Enum(AuthProvider), nullable=False)
    provider_user_id = Column(String(256), nullable=False)  # ID from the provider
    provider_data = Column(JSON, nullable=True)  # Provider-specific metadata
    
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    linked_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="auth_providers")
    
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_auth_provider_user"),
        Index("ix_auth_providers_user", "user_id"),
    )


# ============================================================
# LEDGER SYSTEM - Double-Entry Bookkeeping
# ============================================================

class UserBalance(Base):
    """
    User Balance per Currency (Derived from Ledger)
    This is a cached/materialized view for fast reads
    """
    __tablename__ = "user_balances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyType), nullable=False)
    
    # Balances
    available = Column(Numeric(20, 8), default=0)  # 可用餘額
    frozen = Column(Numeric(20, 8), default=0)     # 凍結餘額 (pending withdrawals, etc.)
    total = Column(Numeric(20, 8), default=0)      # 總餘額 = available + frozen
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="balances")
    
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_user_balance_currency"),
        Index("ix_user_balances_user", "user_id"),
    )


class LedgerEntry(Base):
    """
    Double-Entry Ledger
    Every transaction creates TWO entries: one CREDIT and one DEBIT
    """
    __tablename__ = "ledger_entries"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # Transaction Reference (groups related entries)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # User & Account
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyType), nullable=False)
    
    # Entry Type
    entry_type = Column(Enum(LedgerEntryType), nullable=False)  # credit or debit
    category = Column(Enum(LedgerCategory), nullable=False)
    
    # Amount
    amount = Column(Numeric(20, 8), nullable=False)
    
    # Balance Snapshot (for audit trail)
    balance_before = Column(Numeric(20, 8), nullable=False)
    balance_after = Column(Numeric(20, 8), nullable=False)
    
    # Reference
    ref_type = Column(String(32), nullable=True)  # red_packet, payment, etc.
    ref_id = Column(String(64), nullable=True)    # UUID of the referenced entity
    
    # Metadata
    description = Column(String(512), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Status
    is_reverted = Column(Boolean, default=False)
    reverted_by_id = Column(BigInteger, nullable=True)  # Reference to reverting entry
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ledger_entries")
    
    __table_args__ = (
        Index("ix_ledger_transaction", "transaction_id"),
        Index("ix_ledger_user_currency", "user_id", "currency"),
        Index("ix_ledger_category", "category"),
        Index("ix_ledger_ref", "ref_type", "ref_id"),
        Index("ix_ledger_created", "created_at"),
    )


# ============================================================
# FIAT PAYMENT GATEWAY
# ============================================================

class FiatPayment(Base):
    """
    Fiat Payment Records
    Tracks deposits from UnionPay, Alipay, etc.
    """
    __tablename__ = "fiat_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment Details
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_order_id = Column(String(128), nullable=True, index=True)  # ID from payment provider
    
    # Fiat Side
    fiat_currency = Column(String(8), nullable=False)  # CNY, USD, etc.
    fiat_amount = Column(Numeric(20, 2), nullable=False)
    
    # Crypto Side (after conversion)
    crypto_currency = Column(Enum(CurrencyType), nullable=True)
    crypto_amount = Column(Numeric(20, 8), nullable=True)
    exchange_rate = Column(Numeric(20, 8), nullable=True)  # 1 USDT = ? CNY
    
    # Fees
    provider_fee = Column(Numeric(20, 4), default=0)  # Fee charged by payment provider
    platform_fee = Column(Numeric(20, 4), default=0)  # Our platform fee
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    failure_reason = Column(Text, nullable=True)
    
    # Webhook Data
    webhook_payload = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_fiat_payments_user", "user_id"),
        Index("ix_fiat_payments_status", "status"),
        Index("ix_fiat_payments_provider_order", "provider", "provider_order_id"),
    )


class ExchangeRate(Base):
    """
    Exchange Rate Cache
    Updated periodically from oracle/API
    """
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    from_currency = Column(String(8), nullable=False)
    to_currency = Column(String(8), nullable=False)
    rate = Column(Numeric(20, 8), nullable=False)
    
    source = Column(String(64), nullable=True)  # binance, coingecko, etc.
    
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", name="uq_exchange_rate_pair"),
        Index("ix_exchange_rates_pair", "from_currency", "to_currency"),
    )


# ============================================================
# RED PACKET (Updated)
# ============================================================

class RedPacket(Base):
    """Red Packet - Updated for cross-platform support"""
    __tablename__ = "red_packets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Sender
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender = relationship("User", back_populates="sent_packets", foreign_keys=[sender_id])
    
    # Target (supports multiple platforms)
    platform = Column(String(32), default="telegram")  # telegram, web, whatsapp, etc.
    chat_id = Column(BigInteger, nullable=True)  # Telegram chat ID
    chat_title = Column(String(256), nullable=True)
    share_url = Column(String(512), nullable=True)  # Universal share URL
    
    # Red Packet Config
    currency = Column(Enum(CurrencyType), default=CurrencyType.USDT)
    packet_type = Column(String(32), default="random")  # random, equal, exclusive
    total_amount = Column(Numeric(20, 8), nullable=False)
    total_count = Column(Integer, nullable=False)
    claimed_amount = Column(Numeric(20, 8), default=0)
    claimed_count = Column(Integer, default=0)
    
    # Message
    message = Column(String(256), default="恭喜發財！🧧")
    cover_image = Column(String(512), nullable=True)  # Custom cover
    
    # Game Features
    bomb_number = Column(Integer, nullable=True)  # For bomb packet
    
    # Ledger Reference
    ledger_transaction_id = Column(UUID(as_uuid=True), nullable=True)  # Links to ledger
    
    # Status
    status = Column(String(32), default="active")
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_red_packets_uuid", "uuid"),
        Index("ix_red_packets_sender", "sender_id"),
        Index("ix_red_packets_status", "status"),
        Index("ix_red_packets_share_url", "share_url"),
    )


# ============================================================
# REFERRAL SYSTEM
# ============================================================

class ReferralLink(Base):
    """
    Referral Links for cross-platform tracking
    """
    __tablename__ = "referral_links"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Link Config
    code = Column(String(32), unique=True, nullable=False, index=True)
    platform = Column(String(32), nullable=True)  # twitter, facebook, whatsapp, etc.
    campaign = Column(String(64), nullable=True)  # Campaign identifier
    
    # Stats
    click_count = Column(Integer, default=0)
    signup_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_referral_links_user", "user_id"),
        Index("ix_referral_links_code", "code"),
    )


class ReferralEvent(Base):
    """
    Referral Events (clicks, signups, rewards)
    """
    __tablename__ = "referral_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    link_id = Column(Integer, ForeignKey("referral_links.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    event_type = Column(String(32), nullable=False)  # click, signup, first_deposit, etc.
    
    # Reward
    reward_amount = Column(Numeric(20, 8), nullable=True)
    reward_currency = Column(Enum(CurrencyType), nullable=True)
    reward_paid = Column(Boolean, default=False)
    
    # Metadata
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_referral_events_link", "link_id"),
        Index("ix_referral_events_referred", "referred_user_id"),
    )


# ============================================================
# SESSION MANAGEMENT (for Web users)
# ============================================================

class UserSession(Base):
    """
    User Sessions for Web/H5 Access
    """
    __tablename__ = "user_sessions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session Info
    token_hash = Column(String(128), nullable=False, index=True)  # Hashed JWT/session token
    device_id = Column(String(128), nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # Auth Info
    auth_provider = Column(Enum(AuthProvider), nullable=True)
    
    # Location
    ip_address = Column(String(64), nullable=True)
    country_code = Column(String(3), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index("ix_user_sessions_user", "user_id"),
        Index("ix_user_sessions_token", "token_hash"),
        Index("ix_user_sessions_active", "is_active", "expires_at"),
    )
