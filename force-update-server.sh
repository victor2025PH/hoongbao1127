#!/bin/bash
# 強制更新服務器 - 在服務器終端直接執行
# 使用方法：在服務器上執行：bash force-update-server.sh

set -e

echo "=========================================="
echo "  強制更新和重啟服務器"
echo "=========================================="
echo ""

cd /opt/luckyred || { echo "❌ 無法進入 /opt/luckyred"; exit 1; }

# 1. 檢查當前狀態
echo "[1/8] 檢查當前狀態..."
echo "當前 Git 提交:"
git log --oneline -1
echo ""
echo "檢查是否有未提交的更改:"
git status --short
echo ""

# 2. 強制拉取最新代碼
echo "[2/8] 強制拉取最新代碼..."
git fetch origin
git reset --hard origin/master
echo "✅ 代碼已強制更新到最新版本"
echo "最新提交: $(git log --oneline -1)"
echo ""

# 3. 更新 Bot Token
echo "[3/8] 更新 Bot Token..."
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env
echo "✅ Bot Token 已更新:"
grep BOT_TOKEN .env
echo ""

# 4. 停止服務
echo "[4/8] 停止服務..."
sudo systemctl stop luckyred-api luckyred-bot
sleep 2
echo "✅ 服務已停止"
echo ""

# 5. 重啟 API
echo "[5/8] 重啟 API 服務..."
sudo systemctl start luckyred-api
sleep 3
if sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ API 服務運行中"
    sudo systemctl status luckyred-api --no-pager -l | head -5
else
    echo "❌ API 服務啟動失敗"
    sudo systemctl status luckyred-api --no-pager -l | head -10
    exit 1
fi
echo ""

# 6. 重啟 Bot
echo "[6/8] 重啟 Bot 服務..."
sudo systemctl start luckyred-bot
sleep 3
if sudo systemctl is-active --quiet luckyred-bot; then
    echo "✅ Bot 服務運行中"
    sudo systemctl status luckyred-bot --no-pager -l | head -5
else
    echo "❌ Bot 服務啟動失敗"
    sudo systemctl status luckyred-bot --no-pager -l | head -10
    exit 1
fi
echo ""

# 7. 構建前端
echo "[7/8] 清理並重新構建前端..."
cd frontend
sudo rm -rf dist node_modules/.vite
npm run build
if [ -d "dist" ]; then
    echo "✅ 前端構建完成"
    echo "   構建大小: $(du -sh dist | cut -f1)"
else
    echo "❌ 前端構建失敗"
    exit 1
fi
echo ""

# 8. 重載 Nginx
echo "[8/8] 重載 Nginx..."
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
echo "  更新完成！"
echo "=========================================="
echo ""
echo "服務狀態:"
echo "  Bot:   $(sudo systemctl is-active luckyred-bot)"
echo "  API:   $(sudo systemctl is-active luckyred-api)"
echo "  Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "最新代碼版本:"
cd /opt/luckyred
git log --oneline -1
echo ""
echo "Bot Token:"
grep BOT_TOKEN .env | cut -d'=' -f2 | cut -c1-30
echo "..."

