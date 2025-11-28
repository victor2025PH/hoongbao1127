#!/bin/bash
# 部署腳本 - 在服務器上執行

echo "=========================================="
echo "  部署 Lucky Red 更新"
echo "=========================================="
echo ""

# 進入項目目錄
cd /opt/luckyred || exit 1

# 拉取最新代碼
echo "[1/5] 拉取最新代碼..."
git pull origin master
if [ $? -ne 0 ]; then
    echo "❌ Git pull 失敗"
    exit 1
fi
echo "✅ 代碼更新完成"
echo ""

# 重啟 API 服務
echo "[2/5] 重啟 API 服務..."
sudo systemctl restart luckyred-api
if [ $? -eq 0 ]; then
    echo "✅ API 服務已重啟"
    sleep 2
    sudo systemctl status luckyred-api --no-pager -l | head -5
else
    echo "❌ API 服務重啟失敗"
fi
echo ""

# 重啟 Bot 服務
echo "[3/5] 重啟 Bot 服務..."
sudo systemctl restart luckyred-bot
if [ $? -eq 0 ]; then
    echo "✅ Bot 服務已重啟"
    sleep 2
    sudo systemctl status luckyred-bot --no-pager -l | head -5
else
    echo "❌ Bot 服務重啟失敗"
fi
echo ""

# 構建前端
echo "[4/5] 構建前端..."
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

# 重啟 Nginx
echo "[5/5] 重啟 Nginx..."
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
echo "請檢查服務狀態："
echo "  sudo systemctl status luckyred-api"
echo "  sudo systemctl status luckyred-bot"
echo "  sudo systemctl status nginx"
echo ""

