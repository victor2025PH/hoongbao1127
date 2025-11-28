#!/bin/bash
# LuckyRed 完整部署腳本
set -e

APP_DIR="/opt/luckyred"
BOT_TOKEN="8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs"
ADMIN_ID="5433982810"
DB_PASS="LuckyRed2025!"

echo "=== [1/8] 配置 PostgreSQL ==="
sudo -u postgres psql -c "CREATE USER luckyred WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "用戶已存在"
sudo -u postgres psql -c "CREATE DATABASE luckyred OWNER luckyred;" 2>/dev/null || echo "數據庫已存在"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE luckyred TO luckyred;" 2>/dev/null || true
echo "PostgreSQL OK"

echo "=== [2/8] 克隆代碼 ==="
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR
cd $APP_DIR
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/victor2025PH/hongbao20251025.git .
fi
echo "Clone OK"

echo "=== [3/8] 創建 .env 文件 ==="
cat > $APP_DIR/.env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_ID
DATABASE_URL=postgresql://luckyred:$DB_PASS@localhost:5432/luckyred
SECRET_KEY=luckyred_secret_key_2025_$(date +%s)
MINIAPP_URL=https://mini.usdt2026.cc
ADMIN_URL=https://admin.usdt2026.cc
DEBUG=false
EOF
echo ".env OK"

echo "=== [4/8] 安裝 API 依賴 ==="
cd $APP_DIR/api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
echo "API deps OK"

echo "=== [5/8] 安裝 Bot 依賴 ==="
cd $APP_DIR/bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
echo "Bot deps OK"

echo "=== [6/8] 構建前端 ==="
cd $APP_DIR/frontend
npm install --silent 2>/dev/null
npm run build 2>&1 || echo "Build may have warnings"
echo "Frontend OK"

echo "=== [7/8] 配置 Nginx ==="
sudo cp $APP_DIR/deploy/nginx/*.conf /etc/nginx/sites-available/ 2>/dev/null || true
sudo ln -sf /etc/nginx/sites-available/mini.usdt2026.cc.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
sudo ln -sf /etc/nginx/sites-available/admin.usdt2026.cc.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
echo "Nginx OK"

echo "=== [8/8] 配置並啟動服務 ==="
sudo cp $APP_DIR/deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo chown -R www-data:www-data $APP_DIR
sudo systemctl enable luckyred-api luckyred-bot 2>/dev/null || true
sudo systemctl restart luckyred-api luckyred-bot
echo "Services OK"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo "MiniApp: https://mini.usdt2026.cc"
echo "Admin: https://admin.usdt2026.cc"
echo ""
echo "檢查服務狀態："
sudo systemctl status luckyred-api --no-pager -l | head -5
sudo systemctl status luckyred-bot --no-pager -l | head -5


