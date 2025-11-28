#!/bin/bash
# LuckyRed 完整部署腳本
# 服務器: ubuntu@165.154.254.99
# 域名: mini.usdt2026.cc, admin.usdt2026.cc, bot.usdt2026.cc

set -e

echo "=========================================="
echo "  LuckyRed 完整自動部署"
echo "=========================================="

APP_DIR="/opt/luckyred"
REPO_URL="https://github.com/victor2025PH/hoongbao1127.git"

# 1. 系統更新和依賴安裝
echo "[1/12] 安裝系統依賴..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx postgresql postgresql-contrib python3 python3-pip python3-venv nodejs npm git curl net-tools

# 2. 配置 PostgreSQL
echo "[2/12] 配置 PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql -c "CREATE USER luckyred WITH PASSWORD 'LuckyRed2025!';" 2>/dev/null || echo "用戶已存在"
sudo -u postgres psql -c "CREATE DATABASE luckyred OWNER luckyred;" 2>/dev/null || echo "數據庫已存在"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE luckyred TO luckyred;"

# 3. 克隆代碼
echo "[3/12] 克隆代碼..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR
cd $APP_DIR

if [ -d ".git" ]; then
    echo "更新代碼..."
    git fetch origin
    git reset --hard origin/master
else
    echo "克隆代碼..."
    git clone $REPO_URL .
fi

# 4. 創建環境變量文件
echo "[4/12] 創建環境變量文件..."
cat > $APP_DIR/.env << 'ENVEOF'
# Telegram Bot
BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
BOT_USERNAME=luckyred_bot
ADMIN_IDS=5433982810

# Database
DATABASE_URL=postgresql://luckyred:LuckyRed2025!@localhost:5432/luckyred

# Security
SECRET_KEY=luckyred_secret_key_2025_very_secure
JWT_SECRET=luckyred_jwt_secret_2025
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# URLs
BOT_DOMAIN=bot.usdt2026.cc
ADMIN_DOMAIN=admin.usdt2026.cc
MINIAPP_DOMAIN=mini.usdt2026.cc
MINIAPP_URL=https://mini.usdt2026.cc
GAME_URL=https://mini.usdt2026.cc/game

# App
APP_NAME=LuckyRed
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
ENVEOF

# 5. 安裝 API 依賴
echo "[5/12] 安裝 API 依賴..."
cd $APP_DIR/api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install loguru
deactivate

# 6. 安裝 Bot 依賴
echo "[6/12] 安裝 Bot 依賴..."
cd $APP_DIR/bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install loguru pydantic-settings
deactivate

# 7. 構建前端 MiniApp
echo "[7/12] 構建前端 MiniApp..."
cd $APP_DIR/frontend
npm install
npm run build

# 8. 配置 Nginx
echo "[8/12] 配置 Nginx..."

# MiniApp 配置
sudo tee /etc/nginx/sites-available/mini.usdt2026.cc.conf > /dev/null << 'NGINX1'
server {
    listen 80;
    server_name mini.usdt2026.cc;

    root /opt/luckyred/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX1

# Admin 配置
sudo tee /etc/nginx/sites-available/admin.usdt2026.cc.conf > /dev/null << 'NGINX2'
server {
    listen 80;
    server_name admin.usdt2026.cc;

    root /opt/luckyred/admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX2

# Bot Webhook 配置
sudo tee /etc/nginx/sites-available/bot.usdt2026.cc.conf > /dev/null << 'NGINX3'
server {
    listen 80;
    server_name bot.usdt2026.cc;

    location / {
        proxy_pass http://127.0.0.1:8081/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX3

# 啟用站點
sudo ln -sf /etc/nginx/sites-available/mini.usdt2026.cc.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/admin.usdt2026.cc.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/bot.usdt2026.cc.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 測試並重載 Nginx
sudo nginx -t && sudo systemctl reload nginx

# 9. 配置 Systemd 服務
echo "[9/12] 配置 Systemd 服務..."

# API 服務
sudo tee /etc/systemd/system/luckyred-api.service > /dev/null << 'SERVICE1'
[Unit]
Description=LuckyRed MiniApp API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/luckyred/api
Environment="PATH=/opt/luckyred/api/.venv/bin"
EnvironmentFile=/opt/luckyred/.env
ExecStart=/opt/luckyred/api/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE1

# Bot 服務
sudo tee /etc/systemd/system/luckyred-bot.service > /dev/null << 'SERVICE2'
[Unit]
Description=LuckyRed Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/luckyred/bot
Environment="PATH=/opt/luckyred/bot/.venv/bin"
EnvironmentFile=/opt/luckyred/.env
ExecStart=/opt/luckyred/bot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE2

# 10. 設置權限
echo "[10/12] 設置文件權限..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

# 11. 啟動服務
echo "[11/12] 啟動服務..."
sudo systemctl daemon-reload
sudo systemctl enable luckyred-api luckyred-bot
sudo systemctl restart luckyred-api luckyred-bot

# 等待服務啟動
sleep 5

# 12. 獲取 SSL 證書
echo "[12/12] 獲取 SSL 證書..."
sudo certbot --nginx -d mini.usdt2026.cc -d admin.usdt2026.cc -d bot.usdt2026.cc --non-interactive --agree-tos -m admin@usdt2026.cc || echo "SSL 證書獲取可能需要手動處理"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "服務狀態："
sudo systemctl status luckyred-api --no-pager -l | head -10
echo ""
sudo systemctl status luckyred-bot --no-pager -l | head -10
echo ""
echo "訪問地址："
echo "  MiniApp: https://mini.usdt2026.cc"
echo "  Admin:   https://admin.usdt2026.cc"
echo "  Bot:     https://bot.usdt2026.cc"
echo ""
echo "查看日誌："
echo "  sudo journalctl -u luckyred-api -f"
echo "  sudo journalctl -u luckyred-bot -f"
echo ""

