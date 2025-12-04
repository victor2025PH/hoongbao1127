# API 路由結構 V2

**文件路徑：** `c:\hbgm001\docs\architecture\API路由結構_v2.md`

---

## 認證流程

### 雙模式認證架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        認證層                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐        ┌─────────────────┐                │
│  │  Telegram 用戶   │        │   外部用戶       │               │
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
│           │   統一認證層         │                               │
│           │ → 驗證令牌          │                               │
│           │ → 獲取/創建用戶     │                               │
│           │ → 發放會話 JWT      │                               │
│           └─────────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## API 端點

### `/api/v2/auth` - 認證

```
POST   /auth/telegram          # Telegram initData 認證
POST   /auth/social            # 社交登入 (Google/Apple/Email)
POST   /auth/wallet            # Web3 錢包簽名認證
POST   /auth/particle          # Particle Network 認證
POST   /auth/refresh           # 刷新 JWT 令牌
POST   /auth/logout            # 登出 / 使會話失效
GET    /auth/me                # 獲取當前用戶資訊

# 連結/取消連結提供者
POST   /auth/link/telegram     # 將 Telegram 連結到現有帳號
POST   /auth/link/wallet       # 將錢包連結到現有帳號
DELETE /auth/unlink/{provider} # 取消連結某個提供者
```

### `/api/v2/users` - 用戶管理

```
GET    /users/me               # 獲取當前用戶資料
PATCH  /users/me               # 更新資料
GET    /users/me/balances      # 獲取所有餘額
GET    /users/{uuid}           # 根據 UUID 獲取用戶（公開資料）

# 偏好設定
GET    /users/me/preferences
PATCH  /users/me/preferences

# KYC 身份驗證
POST   /users/me/kyc/start     # 開始 KYC 流程
POST   /users/me/kyc/verify    # 提交驗證資料
GET    /users/me/kyc/status    # 獲取 KYC 狀態
```

### `/api/v2/wallet` - 錢包與餘額

```
GET    /wallet/balances                    # 所有幣種餘額
GET    /wallet/balance/{currency}          # 特定幣種餘額
GET    /wallet/history                     # 交易歷史（帳本）

# 內部轉帳（零手續費）
POST   /wallet/transfer                    # 轉帳給其他用戶

# 法幣充值
POST   /wallet/deposit/fiat/create         # 創建法幣充值訂單
GET    /wallet/deposit/fiat/{id}           # 獲取充值狀態
POST   /wallet/deposit/fiat/webhook/{provider}  # 支付回調

# 加密貨幣充值
GET    /wallet/deposit/crypto/address      # 獲取充值地址
POST   /wallet/deposit/crypto/confirm      # 確認鏈上充值

# 提現
POST   /wallet/withdraw/crypto             # 提現到外部錢包
GET    /wallet/withdraw/{id}               # 獲取提現狀態

# 兌換
POST   /wallet/exchange                    # 幣種兌換
GET    /wallet/exchange/rates              # 獲取匯率
```

### `/api/v2/packets` - 紅包

```
# 創建與管理
POST   /packets                            # 創建紅包
GET    /packets/{uuid}                     # 獲取紅包詳情
DELETE /packets/{uuid}                     # 取消/退款（如未領取）

# 領取
POST   /packets/{uuid}/claim               # 領取紅包
GET    /packets/{uuid}/claims              # 列出領取記錄

# 列表
GET    /packets/sent                       # 我發送的紅包
GET    /packets/received                   # 我領取的紅包
GET    /packets/available                  # 可領取的紅包（按聊天）

# 分享
GET    /packets/{uuid}/share-url           # 獲取通用分享網址
```

### `/api/v2/referral` - 推薦系統

```
# 連結
POST   /referral/links                     # 創建推薦連結
GET    /referral/links                     # 我的推薦連結
GET    /referral/links/{code}/stats        # 連結統計

# 著陸頁
GET    /referral/resolve/{code}            # 解析推薦碼
POST   /referral/track                     # 追蹤點擊/註冊事件

# 獎勵
GET    /referral/rewards                   # 我的推薦獎勵
GET    /referral/leaderboard               # 推薦排行榜
```

### `/api/v2/game` - 遊戲與活動

```
# 簽到
POST   /game/checkin                       # 每日簽到
GET    /game/checkin/status                # 簽到狀態
GET    /game/checkin/history               # 簽到歷史

# 幸運轉盤
POST   /game/wheel/spin                    # 轉動轉盤
GET    /game/wheel/config                  # 轉盤配置

# 排行榜
GET    /game/leaderboard/{type}            # type: packets, claims, referrals
```

---

## 請求/響應格式

### 認證標頭

```http
# Telegram Mini App
Authorization: tma <initData>

# JWT (Web/外部)
Authorization: Bearer <jwt_token>
```

### 統一響應格式

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

### 錯誤響應

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

## 中間件堆疊

```python
# 中間件執行順序
1. RequestIdMiddleware      # 添加唯一請求ID
2. CORSMiddleware          # 處理 CORS
3. RateLimitMiddleware     # 速率限制（基於 Redis）
4. AuthMiddleware          # 驗證認證令牌
5. SessionMiddleware       # 載入/創建用戶會話
6. MetricsMiddleware       # 追蹤請求指標
```

---

## Redis 鍵結構

```
# 用戶餘額快取
balance:{user_id}:{currency}

# 紅包剩餘（高並發）
packet:{packet_id}:remaining_count
packet:{packet_id}:remaining_amount
packet:{packet_id}:claimed_users (SET)

# 速率限制
ratelimit:{user_id}:{endpoint}

# 會話
session:{session_id}

# 匯率
rate:{from}:{to}
```

---

## 文件結構

```
api/
├── routers/
│   ├── v1/                    # 舊版路由（向後兼容）
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── ...
│   └── v2/                    # 新版統一路由
│       ├── __init__.py
│       ├── auth.py            # 認證端點
│       ├── users.py           # 用戶管理
│       ├── wallet.py          # 餘額與轉帳
│       ├── packets.py         # 紅包
│       ├── referral.py        # 推薦系統
│       └── game.py            # 遊戲與活動
├── services/
│   ├── ledger_service.py      # 複式記帳
│   ├── redis_packet_service.py # 高並發領取
│   ├── exchange_service.py    # 幣種轉換
│   ├── referral_service.py    # 推薦系統
│   └── payment/
│       ├── base.py            # 支付提供者基類
│       ├── alchemy_pay.py     # Alchemy Pay 整合
│       └── unlimit.py         # Unlimit 整合
├── utils/
│   ├── auth_v2.py             # 統一認證
│   ├── telegram_auth.py       # Telegram 認證
│   ├── social_auth.py         # 社交登入
│   └── wallet_auth.py         # 錢包認證
└── workers/
    ├── claim_sync_worker.py   # Redis → PostgreSQL 同步
    └── rate_update_worker.py  # 匯率更新
```
