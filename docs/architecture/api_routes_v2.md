# API Route Structure V2

## Authentication Flow

### Dual-Mode Authentication

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐        ┌─────────────────┐                │
│  │  Telegram User  │        │   External User  │               │
│  │  (Mini App)     │        │   (Web/H5/PWA)   │               │
│  └────────┬────────┘        └────────┬─────────┘               │
│           │                          │                          │
│           ▼                          ▼                          │
│  ┌─────────────────┐        ┌─────────────────┐                │
│  │ WebApp.initData │        │  Particle/Web3  │                │
│  │ (HMAC-SHA256)   │        │  Auth JWT       │                │
│  └────────┬────────┘        └────────┬─────────┘               │
│           │                          │                          │
│           └──────────┬───────────────┘                          │
│                      ▼                                          │
│           ┌─────────────────────┐                               │
│           │ Unified Auth Layer  │                               │
│           │ → Validate token    │                               │
│           │ → Get/Create User   │                               │
│           │ → Issue Session JWT │                               │
│           └─────────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API Routes

### `/api/v2/auth` - Authentication

```
POST   /auth/telegram          # Telegram initData auth
POST   /auth/social            # Social login (Google/Apple/Email)
POST   /auth/wallet            # Web3 wallet signature auth
POST   /auth/particle          # Particle Network auth
POST   /auth/refresh           # Refresh JWT token
POST   /auth/logout            # Logout / invalidate session
GET    /auth/me                # Get current user info

# Link/Unlink providers
POST   /auth/link/telegram     # Link Telegram to existing account
POST   /auth/link/wallet       # Link wallet to existing account
DELETE /auth/unlink/{provider} # Unlink a provider
```

### `/api/v2/users` - User Management

```
GET    /users/me               # Get current user profile
PATCH  /users/me               # Update profile
GET    /users/me/balances      # Get all balances
GET    /users/{uuid}           # Get user by UUID (public profile)

# Preferences
GET    /users/me/preferences
PATCH  /users/me/preferences

# KYC
POST   /users/me/kyc/start
POST   /users/me/kyc/verify
GET    /users/me/kyc/status
```

### `/api/v2/wallet` - Wallet & Balance

```
GET    /wallet/balances                    # All currency balances
GET    /wallet/balance/{currency}          # Specific currency balance
GET    /wallet/history                     # Transaction history (ledger)

# Internal Transfer (Zero-Fee)
POST   /wallet/transfer                    # Transfer to another user

# Fiat Deposit
POST   /wallet/deposit/fiat/create         # Create fiat deposit order
GET    /wallet/deposit/fiat/{id}           # Get deposit status
POST   /wallet/deposit/fiat/webhook/{provider}  # Payment webhook

# Crypto Deposit
GET    /wallet/deposit/crypto/address      # Get deposit address
POST   /wallet/deposit/crypto/confirm      # Confirm on-chain deposit

# Withdrawal
POST   /wallet/withdraw/crypto             # Withdraw to external wallet
GET    /wallet/withdraw/{id}               # Get withdrawal status

# Exchange
POST   /wallet/exchange                    # Swap currencies
GET    /wallet/exchange/rates              # Get exchange rates
```

### `/api/v2/packets` - Red Packets

```
# Create & Manage
POST   /packets                            # Create red packet
GET    /packets/{uuid}                     # Get packet details
DELETE /packets/{uuid}                     # Cancel/refund (if unclaimed)

# Claim
POST   /packets/{uuid}/claim               # Claim red packet
GET    /packets/{uuid}/claims              # List claims

# Lists
GET    /packets/sent                       # My sent packets
GET    /packets/received                   # My claimed packets
GET    /packets/available                  # Available packets (by chat)

# Share
GET    /packets/{uuid}/share-url           # Get universal share URL
```

### `/api/v2/referral` - Referral System

```
# Links
POST   /referral/links                     # Create referral link
GET    /referral/links                     # My referral links
GET    /referral/links/{code}/stats        # Link statistics

# Landing
GET    /referral/resolve/{code}            # Resolve referral code
POST   /referral/track                     # Track click/signup event

# Rewards
GET    /referral/rewards                   # My referral rewards
GET    /referral/leaderboard               # Top referrers
```

### `/api/v2/game` - Games & Activities

```
# Check-in
POST   /game/checkin
GET    /game/checkin/status
GET    /game/checkin/history

# Lucky Wheel
POST   /game/wheel/spin
GET    /game/wheel/config

# Leaderboard
GET    /game/leaderboard/{type}            # type: packets, claims, referrals
```

---

## Request/Response Format

### Authentication Header

```http
# Telegram Mini App
Authorization: tma <initData>

# JWT (Web/External)
Authorization: Bearer <jwt_token>
```

### Unified Response Format

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2025-12-02T12:00:00Z",
    "request_id": "uuid"
  }
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "餘額不足",
    "details": {
      "required": "100.00",
      "available": "50.00"
    }
  }
}
```

---

## Middleware Stack

```python
# Order of middleware execution
1. RequestIdMiddleware      # Add unique request ID
2. CORSMiddleware          # Handle CORS
3. RateLimitMiddleware     # Rate limiting (Redis-based)
4. AuthMiddleware          # Validate auth token
5. SessionMiddleware       # Load/create user session
6. MetricsMiddleware       # Track request metrics
```

---

## Redis Keys Structure

```
# User Balance Cache
balance:{user_id}:{currency}

# Red Packet Remaining (for high concurrency)
packet:{packet_id}:remaining_count
packet:{packet_id}:remaining_amount
packet:{packet_id}:claimed_users (SET)

# Rate Limiting
ratelimit:{user_id}:{endpoint}

# Session
session:{session_id}

# Exchange Rates
rate:{from}:{to}
```
