# 🏗️ 全球社交金融平台 - 架構設計文檔

**文件路徑：** `c:\hbgm001\docs\architecture\README.md`

---

## 📁 文件清單與路徑

| 文件名稱 | 路徑 | 說明 |
|---------|------|------|
| **README.md** | `c:\hbgm001\docs\architecture\README.md` | 本索引文件 |
| **資料庫模型_v2.py** | `c:\hbgm001\docs\architecture\資料庫模型_v2.py` | 新版資料庫架構（SQLAlchemy） |
| **API路由結構_v2.md** | `c:\hbgm001\docs\architecture\API路由結構_v2.md` | API 端點設計與認證流程 |
| **Redis高並發腳本.lua** | `c:\hbgm001\docs\architecture\Redis高並發腳本.lua` | 高並發紅包領取 Lua 腳本 |
| **實施計劃.md** | `c:\hbgm001\docs\architecture\實施計劃.md` | 10 週開發計劃與任務清單 |
| **現有系統分析與AI對接方案.md** | `c:\hbgm001\docs\architecture\現有系統分析與AI對接方案.md` | 現有功能分析 + AI 對接設計 |
| **AI對接配置說明.md** | `c:\hbgm001\docs\architecture\AI對接配置說明.md` | AI API 使用說明與範例 |

### 已實現的代碼文件

| 文件名稱 | 路徑 | 說明 |
|---------|------|------|
| **ai_api.py** | `c:\hbgm001\api\routers\ai_api.py` | AI 系統對接 API 實現 |

---

## 🎯 四大支柱概覽

### 支柱 1：通用存取（Anywhere 架構）

**目標：** 讓非 Telegram 用戶（WhatsApp/Facebook）能通過 Web 版無縫遊玩

| 功能 | 當前狀態 | 目標狀態 |
|------|---------|---------|
| 用戶認證 | 僅 Telegram (`tg_id`) | 混合身份（Telegram + Email + 錢包） |
| 前端平台 | Telegram Mini App | Mini App + H5/PWA |
| 分享連結 | Telegram 內部 | 跨平台智慧深度連結 |

**關鍵文件：**
- `資料庫模型_v2.py` → `User` 表、`UserAuthProvider` 表
- `API路由結構_v2.md` → `/api/v2/auth/*` 端點

---

### 支柱 2：類幣安鏈下帳本

**目標：** 實現即時、零 Gas、零手續費的用戶間轉帳（類似微信紅包）

| 功能 | 當前狀態 | 目標狀態 |
|------|---------|---------|
| 餘額存儲 | 直接更新 `users.balance_*` | 複式記帳帳本 |
| 紅包領取 | 直接 DB 寫入 | Redis + Lua 原子操作 |
| 交易記錄 | 單一 `transactions` 表 | `ledger_entries` 複式記帳 |

**關鍵文件：**
- `資料庫模型_v2.py` → `LedgerEntry` 表、`UserBalance` 表
- `Redis高並發腳本.lua` → 領取紅包 Lua 腳本

---

### 支柱 3：法幣轉加密閘道

**目標：** 用戶用本地法幣（如銀聯）支付，系統自動轉換為虛擬 USDT

| 功能 | 當前狀態 | 目標狀態 |
|------|---------|---------|
| 充值方式 | 手動加密充值 | 法幣 + 自動轉換 |
| 支付提供者 | 無 | Alchemy Pay / Unlimit |
| Gas 費用 | 用戶承擔 | 平台內完全免費 |

**流程：**
```
用戶支付 100 CNY (銀聯)
    ↓
Webhook 確認支付
    ↓
獲取 USDT 匯率 (7.4)
    ↓
計算加密金額 (13.5 USDT)
    ↓
貸記用戶帳本餘額
```

**關鍵文件：**
- `資料庫模型_v2.py` → `FiatPayment` 表、`ExchangeRate` 表
- `API路由結構_v2.md` → `/api/v2/wallet/deposit/fiat/*` 端點

---

### 支柱 4：病毒式社交功能

**目標：** 激勵跨平台分享

| 功能 | 當前狀態 | 目標狀態 |
|------|---------|---------|
| 推薦連結 | 基礎邀請碼 | 多平台追蹤連結 |
| 獎勵機制 | 固定獎勵 | 動態佣金（首充 %） |
| 分享卡片 | 無 | OG 圖片生成 |

**關鍵文件：**
- `資料庫模型_v2.py` → `ReferralLink` 表、`ReferralEvent` 表
- `API路由結構_v2.md` → `/api/v2/referral/*` 端點

---

## 🗂️ 新增資料表摘要

| 表名 | 用途 | 關鍵欄位 |
|------|------|---------|
| `users` (擴展) | 統一身份 | `uuid`, `email`, `wallet_address` |
| `user_auth_providers` | 認證提供者連結 | `provider`, `provider_user_id` |
| `user_balances` | 餘額快取 | `available`, `frozen`, `total` |
| `ledger_entries` | 複式記帳 | `entry_type`, `balance_before`, `balance_after` |
| `fiat_payments` | 法幣支付 | `fiat_amount`, `crypto_amount`, `exchange_rate` |
| `exchange_rates` | 匯率快取 | `from_currency`, `to_currency`, `rate` |
| `referral_links` | 推薦連結 | `code`, `platform`, `campaign` |
| `referral_events` | 推薦事件 | `event_type`, `reward_amount` |
| `user_sessions` | 用戶會話 | `token_hash`, `expires_at` |

---

## 🔧 技術棧

### 後端
- **框架：** FastAPI (Python 3.11+)
- **資料庫：** PostgreSQL 15
- **快取：** Redis 7 (Cluster/Sentinel)
- **訊息佇列：** BullMQ / RabbitMQ
- **ORM：** SQLAlchemy 2.0 + Alembic

### 前端
- **框架：** React 18 + TypeScript
- **狀態管理：** Zustand
- **認證：** Particle Network / Web3Auth
- **打包：** Vite

### 基礎設施
- **容器：** Docker + Docker Compose
- **反向代理：** Nginx
- **監控：** Prometheus + Grafana
- **日誌：** ELK Stack

---

## 🚀 快速開始

### 1. 閱讀架構文檔

```bash
# 查看資料庫模型
code c:\hbgm001\docs\architecture\資料庫模型_v2.py

# 查看 API 路由
code c:\hbgm001\docs\architecture\API路由結構_v2.md

# 查看實施計劃
code c:\hbgm001\docs\architecture\實施計劃.md
```

### 2. 開始第一階段

```bash
# 創建遷移
cd c:\hbgm001
alembic revision --autogenerate -m "v2_universal_identity"

# 執行遷移
alembic upgrade head
```

### 3. 設置 Redis

```bash
# Docker 啟動 Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 或使用 Redis Stack（帶 RedisJSON）
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

---

## 📞 聯繫方式

如有問題，請聯繫架構師或在 Issue 中提出。
