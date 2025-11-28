#!/bin/bash
# 在服務器上直接執行的部署腳本
# 使用方法：在服務器終端執行：bash deploy-on-server.sh

set -e

echo "=========================================="
echo "  全自動部署 Lucky Red MiniApp"
echo "=========================================="
echo ""

cd /opt/luckyred || { echo "❌ 無法進入 /opt/luckyred 目錄"; exit 1; }

# 1. 拉取代碼
echo "[1/6] 拉取最新代碼..."
git pull origin master
echo "✅ 代碼更新完成"
echo ""

# 2. 更新 Bot Token
echo "[2/6] 更新 Bot Token..."
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env
echo "✅ Bot Token 已更新: $(grep BOT_TOKEN .env | cut -d'=' -f2 | cut -c1-20)..."
echo ""

# 3. 重啟 API
echo "[3/6] 重啟 API 服務..."
sudo systemctl restart luckyred-api
sleep 2
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ API 服務運行中"
else
    echo "❌ API 服務啟動失敗"
    sudo systemctl status luckyred-api --no-pager -l | head -10
    exit 1
fi
echo ""

# 4. 重啟 Bot
echo "[4/6] 重啟 Bot 服務..."
sudo systemctl restart luckyred-bot
sleep 2
if sudo systemctl is-active --quiet luckyred-bot; then
    echo "✅ Bot 服務運行中"
else
    echo "❌ Bot 服務啟動失敗"
    sudo systemctl status luckyred-bot --no-pager -l | head -10
    exit 1
fi
echo ""

# 5. 構建前端
echo "[5/6] 構建前端（這可能需要幾分鐘）..."
cd frontend
sudo rm -rf dist
npm run build
if [ -d "dist" ]; then
    echo "✅ 前端構建完成"
    echo "   構建文件: $(du -sh dist | cut -f1)"
else
    echo "❌ 前端構建失敗"
    exit 1
fi
echo ""

# 6. 重載 Nginx
echo "[6/6] 重載 Nginx..."
sudo systemctl reload nginx
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 運行中"
else
    echo "❌ Nginx 未運行"
    exit 1
fi
echo ""

# 最終狀態
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "服務狀態:"
echo "  Bot:   $(sudo systemctl is-active luckyred-bot)"
echo "  API:   $(sudo systemctl is-active luckyred-api)"
echo "  Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "請測試以下功能："
echo "  1. 群組搜索功能"
echo "  2. 發送紅包功能"
echo "  3. 機器人不在群組時的處理"
echo ""

