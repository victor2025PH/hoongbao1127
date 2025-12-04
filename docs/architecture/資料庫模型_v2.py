"""
全球社交金融平台 - 資料庫架構 V2
支援：通用存取 + 鏈下帳本 + 法幣閘道

文件路徑：c:\hbgm001\docs\architecture\資料庫模型_v2.py
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
# 列舉類型
# ============================================================

class AuthProvider(str, enum.Enum):
    """認證提供者"""
    TELEGRAM = "telegram"      # Telegram 登入
    GOOGLE = "google"          # Google 登入
    APPLE = "apple"            # Apple 登入
    EMAIL = "email"            # 電子郵件登入
    PHONE = "phone"            # 手機號碼登入
    WALLET = "wallet"          # Web3 錢包登入 (MetaMask 等)
    PARTICLE = "particle"      # Particle Network
    WEB3AUTH = "web3auth"      # Web3Auth


class CurrencyType(str, enum.Enum):
    """貨幣類型"""
    USDT = "usdt"              # 泰達幣
    TON = "ton"                # TON 幣
    STARS = "stars"           # Telegram Stars
    POINTS = "points"         # 平台積分
    CNY = "cny"               # 法幣：人民幣
    USD = "usd"               # 法幣：美元
    TWD = "twd"               # 法幣：新台幣


class LedgerEntryType(str, enum.Enum):
    """帳本條目類型（複式記帳）"""
    CREDIT = "credit"          # 貸方（增加）
    DEBIT = "debit"            # 借方（減少）


class LedgerCategory(str, enum.Enum):
    """帳本類別"""
    # 紅包相關
    PACKET_SEND = "packet_send"           # 發送紅包
    PACKET_CLAIM = "packet_claim"         # 領取紅包
    PACKET_REFUND = "packet_refund"       # 紅包退款
    
    # 轉帳相關
    TRANSFER_IN = "transfer_in"           # 轉入
    TRANSFER_OUT = "transfer_out"         # 轉出
    
    # 法幣相關
    FIAT_DEPOSIT = "fiat_deposit"         # 法幣充值
    FIAT_WITHDRAWAL = "fiat_withdrawal"   # 法幣提現
    
    # 加密貨幣相關
    CRYPTO_DEPOSIT = "crypto_deposit"     # 加密貨幣充值
    CRYPTO_WITHDRAWAL = "crypto_withdrawal" # 加密貨幣提現
    
    # 兌換相關
    SWAP_FROM = "swap_from"               # 兌換來源
    SWAP_TO = "swap_to"                   # 兌換目標
    
    # 獎勵相關
    CHECKIN_REWARD = "checkin_reward"     # 簽到獎勵
    REFERRAL_BONUS = "referral_bonus"     # 推薦獎勵
    GAME_REWARD = "game_reward"           # 遊戲獎勵
    
    # 手續費
    PLATFORM_FEE = "platform_fee"         # 平台手續費
    WITHDRAWAL_FEE = "withdrawal_fee"     # 提現手續費


class PaymentProvider(str, enum.Enum):
    """支付提供者"""
    ALCHEMY_PAY = "alchemy_pay"   # Alchemy Pay
    UNLIMIT = "unlimit"           # Unlimit
    STRIPE = "stripe"             # Stripe
    UNIONPAY = "unionpay"         # 銀聯
    WECHAT = "wechat"             # 微信支付
    ALIPAY = "alipay"             # 支付寶


class PaymentStatus(str, enum.Enum):
    """支付狀態"""
    PENDING = "pending"           # 待處理
    PROCESSING = "processing"     # 處理中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失敗
    CANCELLED = "cancelled"       # 已取消
    REFUNDED = "refunded"         # 已退款


class IdentityStatus(str, enum.Enum):
    """身份驗證狀態"""
    UNVERIFIED = "unverified"     # 未驗證
    PENDING = "pending"           # 審核中
    VERIFIED = "verified"         # 已驗證
    REJECTED = "rejected"         # 已拒絕


# ============================================================
# 核心表 - 統一身份系統
# ============================================================

class User(Base):
    """
    統一用戶實體
    支援混合身份：Telegram、社交登入、Web3 錢包
    
    重要：至少需要一個身份標識（tg_id / email / wallet_address）
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # ===== 主要身份（至少需要一個）=====
    
    # Telegram 身份
    tg_id = Column(BigInteger, unique=True, nullable=True, index=True)
    tg_username = Column(String(64), nullable=True, index=True)
    tg_first_name = Column(String(64), nullable=True)
    tg_last_name = Column(String(64), nullable=True)
    tg_photo_url = Column(String(512), nullable=True)
    
    # 電子郵件/手機（社交登入）
    email = Column(String(256), unique=True, nullable=True, index=True)
    email_verified = Column(Boolean, default=False)
    phone = Column(String(32), unique=True, nullable=True, index=True)
    phone_verified = Column(Boolean, default=False)
    
    # Web3 錢包
    wallet_address = Column(String(64), unique=True, nullable=True, index=True)
    wallet_chain = Column(String(32), nullable=True)  # ethereum, ton, solana 等
    
    # ===== 個人資料 =====
    display_name = Column(String(128), nullable=True)      # 顯示名稱
    avatar_url = Column(String(512), nullable=True)        # 頭像網址
    language_code = Column(String(10), default="zh-TW")    # 語言代碼
    timezone = Column(String(64), default="Asia/Taipei")   # 時區
    
    # ===== KYC / 身份驗證 =====
    identity_status = Column(Enum(IdentityStatus), default=IdentityStatus.UNVERIFIED)
    kyc_level = Column(Integer, default=0)                 # 0: 無, 1: 基礎, 2: 進階
    country_code = Column(String(3), nullable=True)        # ISO 3166-1 alpha-2
    
    # ===== 等級與經驗 =====
    level = Column(Integer, default=1)
    xp = Column(BigInteger, default=0)
    
    # ===== 推薦系統 =====
    invite_code = Column(String(16), unique=True, nullable=True, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invite_count = Column(Integer, default=0)
    total_referral_earnings = Column(Numeric(20, 8), default=0)
    
    # ===== 偏好設定 =====
    interaction_mode = Column(String(20), default="auto")
    notification_enabled = Column(Boolean, default=True)
    
    # ===== 狀態 =====
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    
    # ===== 時間戳 =====
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ===== 關聯 =====
    auth_providers = relationship("UserAuthProvider", back_populates="user")
    balances = relationship("UserBalance", back_populates="user")
    ledger_entries = relationship("LedgerEntry", back_populates="user")
    sent_packets = relationship("RedPacket", back_populates="sender", foreign_keys="RedPacket.sender_id")
    
    __table_args__ = (
        Index("ix_users_uuid", "uuid"),
        Index("ix_users_email_verified", "email", "email_verified"),
        Index("ix_users_wallet", "wallet_address", "wallet_chain"),
        # 至少需要一個身份標識
        CheckConstraint(
            "(tg_id IS NOT NULL) OR (email IS NOT NULL) OR (wallet_address IS NOT NULL)",
            name="ck_users_identity_required"
        ),
    )


class UserAuthProvider(Base):
    """
    連結的認證提供者
    一個用戶可以連結多種認證方式
    """
    __tablename__ = "user_auth_providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    provider = Column(Enum(AuthProvider), nullable=False)           # 提供者類型
    provider_user_id = Column(String(256), nullable=False)          # 提供者的用戶ID
    provider_data = Column(JSON, nullable=True)                     # 提供者特定的元數據
    
    access_token = Column(Text, nullable=True)                      # 存取令牌
    refresh_token = Column(Text, nullable=True)                     # 刷新令牌
    token_expires_at = Column(DateTime, nullable=True)              # 令牌過期時間
    
    linked_at = Column(DateTime, default=datetime.utcnow)           # 連結時間
    last_used_at = Column(DateTime, nullable=True)                  # 最後使用時間
    
    # 關聯
    user = relationship("User", back_populates="auth_providers")
    
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_auth_provider_user"),
        Index("ix_auth_providers_user", "user_id"),
    )


# ============================================================
# 帳本系統 - 複式記帳
# ============================================================

class UserBalance(Base):
    """
    用戶餘額（按幣種）
    這是從帳本衍生的快取/物化視圖，用於快速讀取
    """
    __tablename__ = "user_balances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyType), nullable=False)
    
    # 餘額
    available = Column(Numeric(20, 8), default=0)      # 可用餘額
    frozen = Column(Numeric(20, 8), default=0)         # 凍結餘額（待處理的提現等）
    total = Column(Numeric(20, 8), default=0)          # 總餘額 = available + frozen
    
    # 時間戳
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="balances")
    
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_user_balance_currency"),
        Index("ix_user_balances_user", "user_id"),
    )


class LedgerEntry(Base):
    """
    複式記帳帳本
    每筆交易產生兩條記錄：一條貸方(CREDIT)和一條借方(DEBIT)
    
    範例：用戶A 轉帳 100 USDT 給 用戶B
    - 記錄1: 用戶A, DEBIT, 100 USDT, category=TRANSFER_OUT
    - 記錄2: 用戶B, CREDIT, 100 USDT, category=TRANSFER_IN
    - 兩條記錄共用相同的 transaction_id
    """
    __tablename__ = "ledger_entries"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # 交易參考（將相關條目分組）
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 用戶與帳戶
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyType), nullable=False)
    
    # 條目類型
    entry_type = Column(Enum(LedgerEntryType), nullable=False)  # credit 或 debit
    category = Column(Enum(LedgerCategory), nullable=False)
    
    # 金額
    amount = Column(Numeric(20, 8), nullable=False)
    
    # 餘額快照（用於審計追蹤）
    balance_before = Column(Numeric(20, 8), nullable=False)
    balance_after = Column(Numeric(20, 8), nullable=False)
    
    # 參考
    ref_type = Column(String(32), nullable=True)      # red_packet, payment 等
    ref_id = Column(String(64), nullable=True)        # 參考實體的 UUID
    
    # 元數據
    description = Column(String(512), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # 狀態
    is_reverted = Column(Boolean, default=False)               # 是否已撤銷
    reverted_by_id = Column(BigInteger, nullable=True)         # 撤銷該筆記錄的條目ID
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="ledger_entries")
    
    __table_args__ = (
        Index("ix_ledger_transaction", "transaction_id"),
        Index("ix_ledger_user_currency", "user_id", "currency"),
        Index("ix_ledger_category", "category"),
        Index("ix_ledger_ref", "ref_type", "ref_id"),
        Index("ix_ledger_created", "created_at"),
    )


# ============================================================
# 法幣支付閘道
# ============================================================

class FiatPayment(Base):
    """
    法幣支付記錄
    追蹤來自銀聯、支付寶等的充值
    """
    __tablename__ = "fiat_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # 用戶
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 支付詳情
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_order_id = Column(String(128), nullable=True, index=True)  # 支付提供者的訂單ID
    
    # 法幣端
    fiat_currency = Column(String(8), nullable=False)          # CNY, USD, TWD 等
    fiat_amount = Column(Numeric(20, 2), nullable=False)       # 法幣金額
    
    # 加密貨幣端（轉換後）
    crypto_currency = Column(Enum(CurrencyType), nullable=True)
    crypto_amount = Column(Numeric(20, 8), nullable=True)      # 轉換後的加密貨幣金額
    exchange_rate = Column(Numeric(20, 8), nullable=True)      # 1 USDT = ? CNY
    
    # 手續費
    provider_fee = Column(Numeric(20, 4), default=0)           # 支付提供者收取的手續費
    platform_fee = Column(Numeric(20, 4), default=0)           # 平台手續費
    
    # 狀態
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    failure_reason = Column(Text, nullable=True)
    
    # Webhook 數據
    webhook_payload = Column(JSON, nullable=True)
    
    # 時間戳
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
    匯率快取
    定期從預言機/API 更新
    """
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    from_currency = Column(String(8), nullable=False)          # 來源幣種
    to_currency = Column(String(8), nullable=False)            # 目標幣種
    rate = Column(Numeric(20, 8), nullable=False)              # 匯率
    
    source = Column(String(64), nullable=True)                 # binance, coingecko 等
    
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", name="uq_exchange_rate_pair"),
        Index("ix_exchange_rates_pair", "from_currency", "to_currency"),
    )


# ============================================================
# 紅包（更新版）
# ============================================================

class RedPacket(Base):
    """紅包 - 更新版，支援跨平台"""
    __tablename__ = "red_packets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # 發送者
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender = relationship("User", back_populates="sent_packets", foreign_keys=[sender_id])
    
    # 目標（支援多平台）
    platform = Column(String(32), default="telegram")          # telegram, web, whatsapp 等
    chat_id = Column(BigInteger, nullable=True)                # Telegram 聊天 ID
    chat_title = Column(String(256), nullable=True)
    share_url = Column(String(512), nullable=True)             # 通用分享網址
    
    # 紅包配置
    currency = Column(Enum(CurrencyType), default=CurrencyType.USDT)
    packet_type = Column(String(32), default="random")         # random, equal, exclusive
    total_amount = Column(Numeric(20, 8), nullable=False)
    total_count = Column(Integer, nullable=False)
    claimed_amount = Column(Numeric(20, 8), default=0)
    claimed_count = Column(Integer, default=0)
    
    # 訊息
    message = Column(String(256), default="恭喜發財！🧧")
    cover_image = Column(String(512), nullable=True)           # 自訂封面
    
    # 遊戲功能
    bomb_number = Column(Integer, nullable=True)               # 炸彈紅包的數字
    
    # 帳本參考
    ledger_transaction_id = Column(UUID(as_uuid=True), nullable=True)  # 連結到帳本
    
    # 狀態
    status = Column(String(32), default="active")
    expires_at = Column(DateTime, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_red_packets_uuid", "uuid"),
        Index("ix_red_packets_sender", "sender_id"),
        Index("ix_red_packets_status", "status"),
        Index("ix_red_packets_share_url", "share_url"),
    )


# ============================================================
# 推薦系統
# ============================================================

class ReferralLink(Base):
    """
    推薦連結
    用於跨平台追蹤
    """
    __tablename__ = "referral_links"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 連結配置
    code = Column(String(32), unique=True, nullable=False, index=True)
    platform = Column(String(32), nullable=True)               # twitter, facebook, whatsapp 等
    campaign = Column(String(64), nullable=True)               # 活動標識
    
    # 統計
    click_count = Column(Integer, default=0)
    signup_count = Column(Integer, default=0)
    
    # 狀態
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_referral_links_user", "user_id"),
        Index("ix_referral_links_code", "code"),
    )


class ReferralEvent(Base):
    """
    推薦事件（點擊、註冊、獎勵）
    """
    __tablename__ = "referral_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    link_id = Column(Integer, ForeignKey("referral_links.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    event_type = Column(String(32), nullable=False)            # click, signup, first_deposit 等
    
    # 獎勵
    reward_amount = Column(Numeric(20, 8), nullable=True)
    reward_currency = Column(Enum(CurrencyType), nullable=True)
    reward_paid = Column(Boolean, default=False)
    
    # 元數據
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_referral_events_link", "link_id"),
        Index("ix_referral_events_referred", "referred_user_id"),
    )


# ============================================================
# 會話管理（Web 用戶）
# ============================================================

class UserSession(Base):
    """
    用戶會話
    用於 Web/H5 存取
    """
    __tablename__ = "user_sessions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 會話資訊
    token_hash = Column(String(128), nullable=False, index=True)   # 雜湊後的 JWT/會話令牌
    device_id = Column(String(128), nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # 認證資訊
    auth_provider = Column(Enum(AuthProvider), nullable=True)
    
    # 位置
    ip_address = Column(String(64), nullable=True)
    country_code = Column(String(3), nullable=True)
    
    # 狀態
    is_active = Column(Boolean, default=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index("ix_user_sessions_user", "user_id"),
        Index("ix_user_sessions_token", "token_hash"),
        Index("ix_user_sessions_active", "is_active", "expires_at"),
    )
