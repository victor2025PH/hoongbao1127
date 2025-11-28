#!/bin/bash
# 服務器完整部署腳本
# 使用方法：ssh ubuntu@165.154.254.99 "bash -s" < 服務器部署.sh

set -e  # 遇到錯誤立即退出

echo "========================================"
echo "  服務器完整部署流程"
echo "========================================"
echo ""

cd /opt/luckyred

# 1. 強制更新代碼
echo "[1/4] 強制更新代碼..."
git fetch origin
git reset --hard origin/master
echo "✅ 代碼已更新到最新版本"
echo ""

# 2. 檢查最新提交
echo "[2/4] 檢查最新提交..."
git log --oneline -1
echo ""

# 3. 重新構建前端
echo "[3/4] 重新構建前端..."
cd frontend
sudo rm -rf dist node_modules/.vite
npm run build
if [ $? -ne 0 ]; then
    echo "❌ 構建失敗！"
    exit 1
fi
echo "✅ 前端構建成功"
echo ""

# 4. 重啟服務（如果需要）
echo "[4/4] 檢查服務狀態..."
sudo systemctl is-active luckyred-api && echo "✅ API 服務運行中" || echo "⚠️  API 服務未運行"
sudo systemctl is-active luckyred-bot && echo "✅ Bot 服務運行中" || echo "⚠️  Bot 服務未運行"
sudo systemctl reload nginx && echo "✅ Nginx 已重載" || echo "⚠️  Nginx 重載失敗"
echo ""

echo "========================================"
echo "  ✅ 部署完成！"
echo "========================================"

