# 🚀 Global Social-Fi Platform - Implementation Plan

## Executive Summary

Transform the current Telegram-only Red Packet game into a **Global Social-Fi Platform** with:
- Universal access (Telegram + Web/H5/PWA)
- Zero-fee internal transfers (Off-chain ledger)
- Fiat-to-crypto gateway (UnionPay, Alipay)
- Cross-platform viral sharing

---

## 📋 Phase Overview

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 1** | 2 weeks | Foundation | Database migration, Auth layer |
| **Phase 2** | 2 weeks | Ledger System | Double-entry bookkeeping, Redis |
| **Phase 3** | 2 weeks | Fiat Gateway | Payment integration |
| **Phase 4** | 2 weeks | Universal Access | H5/PWA, Deep linking |
| **Phase 5** | 1 week | Viral Features | Referral system, Social sharing |
| **Phase 6** | 1 week | Testing & Launch | QA, Performance testing |

**Total: 10 weeks**

---

## 📍 Phase 1: Foundation (Week 1-2)

### 1.1 Database Schema Migration

```bash
# Step 1: Create migration files
alembic revision --autogenerate -m "v2_universal_identity"
alembic revision --autogenerate -m "v2_ledger_system"
alembic revision --autogenerate -m "v2_fiat_payments"
alembic revision --autogenerate -m "v2_referral_system"

# Step 2: Apply migrations (with backup)
pg_dump -h localhost -U postgres luckyred > backup_before_v2.sql
alembic upgrade head
```

#### Tasks:
- [ ] Create new schema file (`schema_v2.py`) ✅ Done
- [ ] Generate Alembic migration scripts
- [ ] Add new columns to existing `users` table:
  - `uuid` (UUID)
  - `email`, `email_verified`
  - `phone`, `phone_verified`
  - `wallet_address`, `wallet_chain`
  - `identity_status`, `kyc_level`
- [ ] Create new tables:
  - `user_auth_providers`
  - `user_balances`
  - `ledger_entries`
  - `fiat_payments`
  - `exchange_rates`
  - `referral_links`
  - `referral_events`
  - `user_sessions`
- [ ] Migrate existing balance data to `user_balances` table
- [ ] Create database indexes for performance

### 1.2 Authentication Layer Refactor

#### File: `api/utils/auth_v2.py`

```python
# New unified auth module structure
api/
├── utils/
│   ├── auth_v2.py              # Unified auth layer
│   ├── telegram_auth.py        # Telegram-specific auth
│   ├── social_auth.py          # Social login (Particle/Web3Auth)
│   └── wallet_auth.py          # Web3 wallet auth
```

#### Tasks:
- [ ] Create `AuthProvider` enum
- [ ] Implement `TelegramAuthHandler`:
  ```python
  async def verify_telegram_init_data(init_data: str) -> Optional[TelegramUser]
  ```
- [ ] Implement `SocialAuthHandler`:
  ```python
  async def verify_particle_token(token: str) -> Optional[SocialUser]
  async def verify_web3auth_token(token: str) -> Optional[SocialUser]
  ```
- [ ] Implement `WalletAuthHandler`:
  ```python
  async def verify_wallet_signature(address: str, message: str, signature: str) -> bool
  ```
- [ ] Create unified `get_current_user` dependency:
  ```python
  async def get_current_user(
      authorization: str = Header(None),
  ) -> User:
      # Auto-detect auth method from header
      if authorization.startswith("tma "):
          return await telegram_auth(authorization[4:])
      elif authorization.startswith("Bearer "):
          return await jwt_auth(authorization[7:])
      raise HTTPException(401, "Invalid authorization")
  ```

### 1.3 API Router Restructure

```
api/routers/
├── v2/
│   ├── __init__.py
│   ├── auth.py           # All auth endpoints
│   ├── users.py          # User management
│   ├── wallet.py         # Balance & transfers
│   ├── packets.py        # Red packets
│   ├── referral.py       # Referral system
│   └── game.py           # Games & activities
```

#### Tasks:
- [ ] Create v2 router structure
- [ ] Keep v1 routes working (backward compatibility)
- [ ] Add API versioning middleware
- [ ] Update OpenAPI docs

---

## 📍 Phase 2: Ledger System (Week 3-4)

### 2.1 Double-Entry Bookkeeping Service

#### File: `api/services/ledger_service.py`

```python
class LedgerService:
    """
    Core ledger operations with ACID guarantees
    """
    
    async def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        currency: CurrencyType,
        amount: Decimal,
        category: LedgerCategory,
        ref_type: str = None,
        ref_id: str = None,
    ) -> UUID:
        """
        Execute a transfer between two users.
        Creates TWO ledger entries (credit + debit) atomically.
        """
        pass
    
    async def credit(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: Decimal,
        category: LedgerCategory,
        ...
    ) -> UUID:
        """Add funds to user balance"""
        pass
    
    async def debit(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: Decimal,
        category: LedgerCategory,
        ...
    ) -> UUID:
        """Remove funds from user balance"""
        pass
    
    async def get_balance(
        self,
        user_id: int,
        currency: CurrencyType,
    ) -> Decimal:
        """Get current balance (from cached UserBalance table)"""
        pass
```

#### Tasks:
- [ ] Implement `LedgerService` class
- [ ] Add database triggers to update `user_balances` on ledger insert
- [ ] Implement balance snapshot in every ledger entry
- [ ] Add audit trail queries
- [ ] Create ledger reconciliation job

### 2.2 Redis High-Concurrency Layer

#### File: `api/services/redis_packet_service.py`

```python
class RedisPacketService:
    """
    High-concurrency red packet claims using Redis + Lua
    """
    
    CLAIM_SCRIPT = """..."""  # Lua script from redis_lua_scripts.lua
    
    async def init_packet(self, packet_id: str, total_count: int, total_amount: Decimal):
        """Initialize packet in Redis when created"""
        pass
    
    async def claim_packet(self, packet_id: str, user_id: int) -> ClaimResult:
        """
        Atomic claim operation in Redis.
        Returns immediately with result.
        Actual DB write happens async.
        """
        pass
    
    async def sync_to_db(self, packet_id: str):
        """
        Background job to sync Redis claims to PostgreSQL.
        Run by worker process.
        """
        pass
```

#### Tasks:
- [ ] Setup Redis connection pool
- [ ] Register Lua scripts
- [ ] Implement `RedisPacketService`
- [ ] Create BullMQ worker for async DB sync:
  ```python
  # worker.py
  async def process_claim_queue():
      while True:
          claim = await redis.blpop("claims_queue")
          await sync_claim_to_postgres(claim)
  ```
- [ ] Add Redis Sentinel/Cluster for HA
- [ ] Implement fallback to direct DB if Redis fails

### 2.3 Balance Cache Layer

```python
class BalanceCache:
    """
    Redis cache for user balances with write-through
    """
    
    async def get_balance(self, user_id: int, currency: str) -> Decimal:
        # Try Redis first
        cached = await redis.get(f"balance:{user_id}:{currency}")
        if cached:
            return Decimal(cached)
        
        # Fallback to DB
        balance = await db_get_balance(user_id, currency)
        await redis.setex(f"balance:{user_id}:{currency}", 300, str(balance))
        return balance
    
    async def invalidate(self, user_id: int, currency: str = None):
        if currency:
            await redis.delete(f"balance:{user_id}:{currency}")
        else:
            # Invalidate all currencies
            for c in CurrencyType:
                await redis.delete(f"balance:{user_id}:{c.value}")
```

---

## 📍 Phase 3: Fiat Gateway (Week 5-6)

### 3.1 Payment Provider Abstraction

#### File: `api/services/payment/base.py`

```python
from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    """Base class for payment providers"""
    
    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        user_id: int,
        return_url: str,
    ) -> PaymentOrder:
        pass
    
    @abstractmethod
    async def verify_webhook(
        self,
        payload: dict,
        signature: str,
    ) -> PaymentResult:
        pass
    
    @abstractmethod
    async def query_order(self, order_id: str) -> PaymentStatus:
        pass
```

### 3.2 Provider Implementations

```
api/services/payment/
├── base.py
├── alchemy_pay.py      # Alchemy Pay integration
├── unlimit.py          # Unlimit integration
└── mock.py             # Mock provider for testing
```

#### Tasks:
- [ ] Implement `AlchemyPayProvider`:
  - [ ] API key management
  - [ ] Order creation
  - [ ] Webhook signature verification
  - [ ] Status polling
- [ ] Implement `UnlimitProvider`
- [ ] Create webhook endpoint:
  ```python
  @router.post("/wallet/deposit/fiat/webhook/{provider}")
  async def payment_webhook(provider: str, request: Request):
      # 1. Verify signature
      # 2. Update FiatPayment status
      # 3. Credit user balance via LedgerService
      # 4. Send notification
  ```

### 3.3 Auto-Conversion Service

#### File: `api/services/exchange_service.py`

```python
class ExchangeService:
    """
    Handles fiat-to-crypto conversion
    """
    
    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get current exchange rate"""
        # Try cache first
        rate = await redis.get(f"rate:{from_currency}:{to_currency}")
        if rate:
            return Decimal(rate)
        
        # Fetch from oracle (Binance, CoinGecko, etc.)
        rate = await self._fetch_rate(from_currency, to_currency)
        await redis.setex(f"rate:{from_currency}:{to_currency}", 60, str(rate))
        return rate
    
    async def convert_fiat_to_crypto(
        self,
        user_id: int,
        fiat_amount: Decimal,
        fiat_currency: str,
        target_crypto: CurrencyType,
    ) -> Decimal:
        """
        Convert fiat payment to crypto credit.
        Called after fiat payment is confirmed.
        """
        rate = await self.get_rate(fiat_currency, target_crypto.value)
        crypto_amount = fiat_amount / rate
        
        # Credit via ledger
        await ledger_service.credit(
            user_id=user_id,
            currency=target_crypto,
            amount=crypto_amount,
            category=LedgerCategory.FIAT_DEPOSIT,
        )
        
        return crypto_amount
```

#### Tasks:
- [ ] Implement `ExchangeService`
- [ ] Setup rate oracle (Binance API / CoinGecko)
- [ ] Create rate update cron job (every 1 minute)
- [ ] Handle rate slippage protection
- [ ] Add admin override for manual rates

---

## 📍 Phase 4: Universal Access (Week 7-8)

### 4.1 Frontend Environment Detection

#### File: `frontend/src/utils/environment.ts`

```typescript
export enum AppEnvironment {
  TELEGRAM_MINIAPP = 'telegram_miniapp',
  WEB_BROWSER = 'web_browser',
  PWA = 'pwa',
}

export function detectEnvironment(): AppEnvironment {
  // Check if running inside Telegram
  if (window.Telegram?.WebApp?.initData) {
    return AppEnvironment.TELEGRAM_MINIAPP;
  }
  
  // Check if PWA
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return AppEnvironment.PWA;
  }
  
  return AppEnvironment.WEB_BROWSER;
}

export function getAuthStrategy(): 'telegram' | 'social' | 'wallet' {
  const env = detectEnvironment();
  
  if (env === AppEnvironment.TELEGRAM_MINIAPP) {
    return 'telegram';
  }
  
  // For web, check if user has connected wallet
  if (localStorage.getItem('wallet_connected')) {
    return 'wallet';
  }
  
  return 'social';
}
```

### 4.2 Dual-Mode Auth Provider

#### File: `frontend/src/providers/AuthProvider.tsx`

```tsx
import { ParticleNetwork } from '@particle-network/auth';
import { Web3Auth } from '@web3auth/modal';

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authMethod, setAuthMethod] = useState<'telegram' | 'social' | 'wallet' | null>(null);
  
  useEffect(() => {
    const init = async () => {
      const env = detectEnvironment();
      
      if (env === AppEnvironment.TELEGRAM_MINIAPP) {
        // Silent auth with Telegram
        const initData = window.Telegram.WebApp.initData;
        const result = await api.post('/auth/telegram', { initData });
        setUser(result.user);
        setAuthMethod('telegram');
      } else {
        // Check existing session
        const session = await checkExistingSession();
        if (session) {
          setUser(session.user);
          setAuthMethod(session.method);
        }
      }
    };
    
    init();
  }, []);
  
  const loginWithSocial = async (provider: 'google' | 'apple' | 'email') => {
    // Use Particle Network
    const particle = new ParticleNetwork({ ... });
    const userInfo = await particle.auth.login({ provider });
    
    const result = await api.post('/auth/social', {
      provider: 'particle',
      token: userInfo.token,
    });
    
    setUser(result.user);
    setAuthMethod('social');
  };
  
  const loginWithWallet = async () => {
    // Use Web3Auth or direct wallet
    const web3auth = new Web3Auth({ ... });
    await web3auth.connect();
    
    // Sign message for auth
    const message = await api.get('/auth/wallet/challenge');
    const signature = await web3auth.signMessage(message);
    
    const result = await api.post('/auth/wallet', {
      address: web3auth.address,
      message,
      signature,
    });
    
    setUser(result.user);
    setAuthMethod('wallet');
  };
  
  return (
    <AuthContext.Provider value={{ user, authMethod, loginWithSocial, loginWithWallet }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 4.3 Smart Deep Linking

#### File: `api/routers/v2/redirect.py`

```python
@router.get("/r/{code}")
async def smart_redirect(code: str, request: Request):
    """
    Universal redirect endpoint.
    Detects client and redirects appropriately.
    """
    user_agent = request.headers.get("user-agent", "").lower()
    
    # Parse the code to determine type
    link = await get_link_by_code(code)
    
    if not link:
        raise HTTPException(404, "Link not found")
    
    # Detect if Telegram app
    is_telegram = "telegram" in user_agent or "tg" in request.query_params
    
    if is_telegram:
        # Redirect to Telegram Mini App
        return RedirectResponse(
            f"https://t.me/{BOT_USERNAME}/app?startapp={code}"
        )
    else:
        # Redirect to H5 web version
        return RedirectResponse(
            f"https://app.yoursite.com/?ref={code}"
        )
```

### 4.4 PWA Configuration

#### File: `frontend/public/manifest.json`

```json
{
  "name": "Lucky Red - Social Fi Platform",
  "short_name": "Lucky Red",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#e94560",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

#### Tasks:
- [ ] Implement environment detection
- [ ] Setup Particle Network SDK
- [ ] Setup Web3Auth SDK (optional)
- [ ] Create login/signup UI for web
- [ ] Implement smart deep linking
- [ ] Configure PWA manifest
- [ ] Add service worker for offline support
- [ ] Test on iOS Safari, Android Chrome

---

## 📍 Phase 5: Viral Features (Week 9)

### 5.1 Referral System

#### File: `api/services/referral_service.py`

```python
class ReferralService:
    """Manages referral links and rewards"""
    
    async def create_link(
        self,
        user_id: int,
        platform: str = None,
        campaign: str = None,
    ) -> ReferralLink:
        """Create a new referral link"""
        code = generate_unique_code()
        link = ReferralLink(
            user_id=user_id,
            code=code,
            platform=platform,
            campaign=campaign,
        )
        await db.save(link)
        return link
    
    async def track_event(
        self,
        code: str,
        event_type: str,  # click, signup, first_deposit
        referred_user_id: int = None,
        metadata: dict = None,
    ):
        """Track referral events"""
        pass
    
    async def calculate_reward(
        self,
        referrer_id: int,
        referred_id: int,
        event_type: str,
    ) -> Decimal:
        """Calculate and credit referral reward"""
        # Get reward config
        config = await get_referral_config()
        
        if event_type == 'signup':
            reward = config.signup_reward  # e.g., 1 USDT
        elif event_type == 'first_deposit':
            # % of first deposit
            deposit = await get_first_deposit(referred_id)
            reward = deposit * config.deposit_commission  # e.g., 5%
        
        # Credit referrer
        await ledger_service.credit(
            user_id=referrer_id,
            currency=CurrencyType.USDT,
            amount=reward,
            category=LedgerCategory.REFERRAL_BONUS,
        )
        
        return reward
```

### 5.2 Social Share Cards

#### File: `api/services/share_service.py`

```python
class ShareService:
    """Generate share content for different platforms"""
    
    async def generate_packet_share(self, packet_id: str) -> ShareContent:
        """Generate share content for a red packet"""
        packet = await get_packet(packet_id)
        
        # Generate OG image
        og_image = await self._generate_og_image(packet)
        
        return ShareContent(
            url=f"https://app.yoursite.com/r/p_{packet_id}",
            title=f"🧧 {packet.message}",
            description=f"Someone sent you a {packet.total_amount} {packet.currency.upper()} red packet!",
            image=og_image,
            # Platform-specific
            twitter_text=f"🧧 I just received a red packet! Grab yours: ",
            whatsapp_text=f"🧧 {packet.message}\n\nClick to claim: ",
        )
```

#### Tasks:
- [ ] Implement `ReferralService`
- [ ] Create referral link generation endpoint
- [ ] Implement click tracking (with rate limiting)
- [ ] Setup reward calculation and payout
- [ ] Create referral leaderboard
- [ ] Generate OG images for social sharing
- [ ] Add share buttons in UI

---

## 📍 Phase 6: Testing & Launch (Week 10)

### 6.1 Testing Checklist

#### Unit Tests
- [ ] Auth handlers (all providers)
- [ ] Ledger service (double-entry integrity)
- [ ] Redis Lua scripts
- [ ] Payment webhook verification
- [ ] Exchange rate service

#### Integration Tests
- [ ] Full payment flow (create → webhook → credit)
- [ ] Red packet flow (create → claim → DB sync)
- [ ] Cross-platform auth (Telegram → link wallet)
- [ ] Referral flow (create link → signup → reward)

#### Load Tests
```bash
# Test red packet claiming at scale
wrk -t12 -c400 -d30s -s claim_packet.lua http://localhost:8080/api/v2/packets/{id}/claim

# Target: 10,000 QPS with p99 < 100ms
```

### 6.2 Monitoring & Alerts

```yaml
# Prometheus alerts
- alert: RedisPacketQueueBacklog
  expr: redis_list_length{key="claims_queue"} > 1000
  for: 5m
  labels:
    severity: warning

- alert: LedgerBalanceMismatch
  expr: ledger_balance_check_failures > 0
  labels:
    severity: critical
```

### 6.3 Launch Checklist

- [ ] Database migrations applied
- [ ] Redis Sentinel configured
- [ ] Payment provider webhooks verified
- [ ] SSL certificates valid
- [ ] Rate limiting configured
- [ ] Monitoring dashboards ready
- [ ] Rollback plan documented
- [ ] On-call rotation scheduled

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐           │
│  │ Telegram Mini   │   │  H5 Web / PWA   │   │  Native Apps    │           │
│  │     App         │   │   (External)    │   │   (Future)      │           │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘           │
│           │                     │                     │                     │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (Nginx)                               │
│                     Rate Limiting, SSL, Load Balancing                      │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Telegram   │  │  Particle   │  │  Web3Auth   │  │   Wallet    │        │
│  │  initData   │  │   Network   │  │    JWT      │  │  Signature  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                           │                                                 │
│                           ▼                                                 │
│                  ┌─────────────────┐                                        │
│                  │ Unified Session │                                        │
│                  │      JWT        │                                        │
│                  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Wallet    │  │  Red Packet │  │   Referral  │  │    Game     │        │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┼────────────────┼────────────────┘                │
│                          │                │                                 │
│                          ▼                ▼                                 │
│                  ┌─────────────────────────────┐                            │
│                  │       LEDGER SERVICE        │                            │
│                  │   (Double-Entry Booking)    │                            │
│                  └─────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   PostgreSQL      │ │   Redis Cluster   │ │   Message Queue   │
│   (Primary DB)    │ │   (Cache + Lock)  │ │   (BullMQ)        │
├───────────────────┤ ├───────────────────┤ ├───────────────────┤
│ • Users           │ │ • Balance Cache   │ │ • Claim Queue     │
│ • Ledger Entries  │ │ • Packet State    │ │ • Webhook Queue   │
│ • Red Packets     │ │ • Rate Limits     │ │ • Notification    │
│ • Payments        │ │ • Sessions        │ │   Queue           │
└───────────────────┘ └───────────────────┘ └───────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                          │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Alchemy Pay │  │  Binance    │  │  Telegram   │            │
│  │   (Fiat)    │  │ (Rates API) │  │   Bot API   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└───────────────────────────────────────────────────────────────┘
```

---

## 📁 Final Directory Structure

```
hbgm001/
├── api/
│   ├── routers/
│   │   ├── v1/                    # Legacy routes (backward compat)
│   │   └── v2/                    # New unified routes
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── wallet.py
│   │       ├── packets.py
│   │       ├── referral.py
│   │       └── game.py
│   ├── services/
│   │   ├── ledger_service.py      # Double-entry bookkeeping
│   │   ├── redis_packet_service.py # High-concurrency claims
│   │   ├── exchange_service.py    # Currency conversion
│   │   ├── referral_service.py    # Referral system
│   │   └── payment/
│   │       ├── base.py
│   │       ├── alchemy_pay.py
│   │       └── unlimit.py
│   ├── utils/
│   │   ├── auth_v2.py             # Unified auth
│   │   └── ...
│   └── workers/
│       ├── claim_sync_worker.py   # Redis → PostgreSQL sync
│       └── rate_update_worker.py  # Exchange rate updates
├── frontend/
│   ├── src/
│   │   ├── providers/
│   │   │   └── AuthProvider.tsx   # Dual-mode auth
│   │   ├── utils/
│   │   │   └── environment.ts     # Environment detection
│   │   └── ...
│   └── public/
│       └── manifest.json          # PWA config
├── shared/
│   └── database/
│       └── models_v2.py           # New schema
├── docs/
│   └── architecture/
│       ├── schema_v2.py           # ✅ Created
│       ├── api_routes_v2.md       # ✅ Created
│       ├── redis_lua_scripts.lua  # ✅ Created
│       └── IMPLEMENTATION_PLAN.md # ✅ Created
└── migrations/
    └── versions/
        └── ...                    # Alembic migrations
```

---

## 🎯 Next Steps

1. **Review this plan** and confirm scope
2. **Start Phase 1**: Database migration
3. **Setup development environment** with Redis
4. **Create feature branches** for parallel development

Shall I start implementing any specific component?
