#!/bin/bash
# 服務器更新代碼並重啟 API 服務
# 使用方法：ssh ubuntu@165.154.254.99 "bash -s" < 服務器更新並重啟.sh

set -e  # 遇到錯誤立即退出

echo "========================================"
echo "  更新代碼並重啟服務"
echo "========================================"
echo ""

cd /opt/luckyred

# 1. 更新代碼
echo "[1/4] 更新代碼..."
git fetch origin
git reset --hard origin/master
echo "✅ 代碼已更新"
echo ""

# 2. 檢查最新提交
echo "[2/4] 檢查最新提交..."
git log --oneline -1
echo ""

# 3. 重啟 API 服務
echo "[3/4] 重啟 API 服務..."
sudo systemctl restart luckyred-api
sleep 2
echo "✅ API 服務已重啟"
echo ""

# 4. 檢查服務狀態
echo "[4/4] 檢查服務狀態..."
sudo systemctl status luckyred-api --no-pager | head -15
echo ""

echo "========================================"
echo "  ✅ 更新完成！"
echo "========================================"

