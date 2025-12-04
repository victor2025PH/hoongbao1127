#!/bin/bash
# Lucky Red 服務器更新腳本
# 在服務器上執行: bash server_update.sh

echo "========================================"
echo "   Lucky Red 服務器更新腳本"
echo "========================================"
echo ""

cd /opt/luckyred

# 1. 拉取最新代碼
echo "[1/3] 拉取最新代碼..."
git pull origin master

# 2. 創建目錄
echo "[2/3] 確保目錄存在..."
mkdir -p /opt/luckyred/api/services

# 3. 重啟服務
echo "[3/3] 重啟服務..."
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
