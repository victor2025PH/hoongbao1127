#!/bin/bash
# MiniApp 部署腳本 - 在服務器上執行

echo "=========================================="
echo "  部署 Lucky Red MiniApp"
echo "=========================================="
echo ""

# 進入項目目錄
cd /opt/luckyred || exit 1

# 1. 拉取最新代碼
echo "[1/6] 拉取最新代碼..."
git pull origin master
if [ $? -ne 0 ]; then
    echo "❌ Git pull 失敗"
    exit 1
fi
echo "✅ 代碼更新完成"
echo ""

# 2. 更新 Bot Token（如果需要）
echo "[2/6] 檢查 Bot Token..."
if grep -q "BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs" .env; then
    echo "✅ Bot Token 已正確配置"
else
    echo "⚠️  更新 Bot Token..."
    sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env
    echo "✅ Bot Token 已更新"
fi
echo ""

# 3. 重啟 API 服務
echo "[3/6] 重啟 API 服務..."
sudo systemctl restart luckyred-api
if [ $? -eq 0 ]; then
    echo "✅ API 服務已重啟"
    sleep 2
    sudo systemctl status luckyred-api --no-pager -l | head -5
else
    echo "❌ API 服務重啟失敗"
fi
echo ""

# 4. 重啟 Bot 服務
echo "[4/6] 重啟 Bot 服務..."
sudo systemctl restart luckyred-bot
if [ $? -eq 0 ]; then
    echo "✅ Bot 服務已重啟"
    sleep 2
    sudo systemctl status luckyred-bot --no-pager -l | head -5
else
    echo "❌ Bot 服務重啟失敗"
fi
echo ""

# 5. 構建前端
echo "[5/6] 構建前端..."
cd frontend || exit 1
sudo rm -rf dist
npm run build
if [ $? -eq 0 ]; then
    echo "✅ 前端構建完成"
else
    echo "❌ 前端構建失敗"
    exit 1
fi
echo ""

# 6. 重載 Nginx
echo "[6/6] 重載 Nginx..."
sudo systemctl reload nginx
if [ $? -eq 0 ]; then
    echo "✅ Nginx 已重載"
else
    echo "❌ Nginx 重載失敗"
fi
echo ""

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "服務狀態："
echo "  Bot:  $(sudo systemctl is-active luckyred-bot)"
echo "  API:  $(sudo systemctl is-active luckyred-api)"
echo "  Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "請測試以下功能："
echo "  1. 群組搜索功能"
echo "  2. 發送紅包功能"
echo "  3. 機器人不在群組時的處理"
echo ""

