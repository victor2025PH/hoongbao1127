# 🚀 Lucky Red 快速部署指南

## 一、本地開發測試

### Windows 環境
```powershell
# 1. 確保 Python 3.10+ 已安裝
python --version

# 2. 啟動服務（自動安裝依賴）
.\start-services.ps1

# 或分別啟動：
# API: cd api && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && uvicorn main:app --host 127.0.0.1 --port 8080 --reload
# Bot: cd bot && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python main.py
```

### 測試
- API 文檔: http://127.0.0.1:8080/docs
- 健康檢查: http://127.0.0.1:8080/health
- Telegram: 發送 `/start` 給你的 Bot

---

## 二、生產環境部署 (Linux)

### 快速部署（推薦）
```bash
# 1. 上傳代碼到服務器
scp -r . user@server:/opt/luckyred/

# 2. SSH 登錄服務器
ssh user@server

# 3. 配置環境變量
cd /opt/luckyred
cp .env.example .env
nano .env  # 編輯配置

# 4. 執行部署腳本
sudo bash deploy/scripts/deploy-full.sh
```

### 手動部署步驟

#### 1. 系統準備
```bash
# 安裝依賴
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx nodejs npm
```

#### 2. 數據庫設置
```bash
# 創建數據庫和用戶
sudo -u postgres psql
CREATE DATABASE luckyred;
CREATE USER luckyred WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE luckyred TO luckyred;
\q
```

#### 3. Python 環境
```bash
# API
cd /opt/luckyred/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

# Bot
cd /opt/luckyred/bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### 4. Systemd 服務
```bash
# 複製服務文件
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable luckyred-api luckyred-bot
sudo systemctl start luckyred-api luckyred-bot
```

#### 5. Nginx 配置
```bash
# 複製配置
sudo cp deploy/nginx/*.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/mini.usdt2026.cc.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. SSL 證書（重要）
```bash
# 安裝 certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d mini.usdt2026.cc
```

#### 7. 前端構建
```bash
cd /opt/luckyred/frontend
npm install
npm run build
```

---

## 三、環境變量配置

必須配置的變量（`.env` 文件）：

```env
# Bot 配置
BOT_TOKEN=your_bot_token_from_botfather
BOT_USERNAME=your_bot_username

# 管理員
ADMIN_IDS=123456789,987654321

# 數據庫
DATABASE_URL=postgresql://luckyred:password@localhost:5432/luckyred

# JWT
JWT_SECRET=your_very_long_random_secret_key

# 域名
API_BASE_URL=https://mini.usdt2026.cc
MINIAPP_URL=https://mini.usdt2026.cc
```

---

## 四、常用管理命令

```bash
# 查看服務狀態
sudo systemctl status luckyred-api luckyred-bot

# 重啟服務
sudo systemctl restart luckyred-api luckyred-bot

# 查看日誌
sudo journalctl -u luckyred-api -f
sudo journalctl -u luckyred-bot -f

# 更新代碼後
cd /opt/luckyred
git pull
sudo systemctl restart luckyred-api luckyred-bot
```

---

## 五、故障排除

### API 無法啟動
```bash
# 檢查日誌
sudo journalctl -u luckyred-api -n 50

# 手動測試
cd /opt/luckyred/api
source .venv/bin/activate
python -c "from shared.database.connection import get_db; print('OK')"
```

### Bot 無法啟動
```bash
# 檢查日誌
sudo journalctl -u luckyred-bot -n 50

# 確認 Token
grep BOT_TOKEN /opt/luckyred/.env
```

### 502 Bad Gateway
```bash
# 檢查 API 是否運行
curl http://127.0.0.1:8080/health

# 檢查 Nginx 配置
sudo nginx -t
sudo systemctl reload nginx
```

---

## 六、檢查清單

部署前：
- [ ] `.env` 文件已配置
- [ ] 數據庫連接測試通過
- [ ] Bot Token 有效

部署後：
- [ ] API 健康檢查通過
- [ ] Bot 響應 `/start`
- [ ] 前端頁面可訪問
- [ ] SSL 證書已配置

---

**完整文檔**: 參考 `deploy/checklist.md` 和 `DEPLOYMENT_GUIDE.md`
