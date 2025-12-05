#!/bin/bash
# Lucky Red 服務器更新腳本
# 在服務器上執行: bash server_update.sh

set -e

echo "========================================"
echo "   Lucky Red 服務器更新腳本"
echo "========================================"
echo ""

cd /opt/luckyred

# 1. 拉取最新代碼
echo "[1/5] 拉取最新代碼..."
git fetch origin
git pull origin master || git pull origin main

# 2. 運行數據庫遷移
echo "[2/5] 運行數據庫遷移..."
cd /opt/luckyred/api
if [ -d ".venv" ]; then
    source .venv/bin/activate
    cd /opt/luckyred
    python3 migrations/add_task_redpacket_system.py || echo "⚠️ 遷移可能已執行過"
    deactivate
else
    cd /opt/luckyred
    python3 migrations/add_task_redpacket_system.py || echo "⚠️ 遷移可能已執行過"
fi

# 3. 安裝API依賴（如果有新依賴）
echo "[3/5] 檢查API依賴..."
cd /opt/luckyred/api
if [ -f "requirements.txt" ]; then
    source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
    pip install -q -r requirements.txt
fi

# 4. 構建前端
echo "[4/5] 構建前端..."
cd /opt/luckyred/frontend
npm install --silent
npm run build

# 5. 重啟服務
echo "[5/5] 重啟服務..."
sudo systemctl restart luckyred-api
sudo systemctl restart luckyred-bot

echo ""
echo "========================================"
echo "   服務器更新完成！"
echo "========================================"

# 顯示服務狀態
echo ""
echo "API 服務狀態:"
sudo systemctl status luckyred-api --no-pager | head -5
echo ""
echo "Bot 服務狀態:"
sudo systemctl status luckyred-bot --no-pager | head -5
