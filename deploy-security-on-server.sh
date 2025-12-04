#!/bin/bash
# ============================================
# 服務器端：安全與合規層部署腳本
# 在服務器上執行此腳本完成部署
# ============================================

set -e

PROJECT_DIR="/opt/luckyred"
cd $PROJECT_DIR

echo "========================================"
echo "  安全與合規層 - 服務器部署"
echo "========================================"

# 1. 執行數據庫遷移
echo ""
echo "[1/5] 執行數據庫遷移..."
if [ -f "migrations/安全與合規層遷移.sql" ]; then
    sudo -u postgres psql -d luckyred -f "migrations/安全與合規層遷移.sql"
    echo "✅ 數據庫遷移完成"
else
    echo "⚠️ 遷移文件不存在，跳過"
fi

# 2. 安裝 Python 依賴（如果有新增）
echo ""
echo "[2/5] 檢查 Python 依賴..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo "✅ Python 依賴已更新"
fi

# 3. 安裝前端依賴
echo ""
echo "[3/5] 安裝前端依賴..."
cd frontend
if [ -f "package.json" ]; then
    npm install @fingerprintjs/fingerprintjs --save
    echo "✅ FingerprintJS 已安裝"
    
    echo "正在重建前端..."
    npm run build
    echo "✅ 前端構建完成"
fi
cd ..

# 4. 重啟服務
echo ""
echo "[4/5] 重啟服務..."
sudo systemctl restart luckyred-api 2>/dev/null || echo "⚠️ luckyred-api 服務不存在"
sudo systemctl restart luckyred-bot 2>/dev/null || echo "⚠️ luckyred-bot 服務不存在"
echo "✅ 服務已重啟"

# 5. 檢查服務狀態
echo ""
echo "[5/5] 檢查服務狀態..."
echo ""
echo "API 服務狀態:"
sudo systemctl status luckyred-api --no-pager -l 2>/dev/null || echo "服務未安裝"
echo ""
echo "Bot 服務狀態:"
sudo systemctl status luckyred-bot --no-pager -l 2>/dev/null || echo "服務未安裝"

echo ""
echo "========================================"
echo "  ✅ 部署完成！"
echo "========================================"
echo ""
echo "新功能已啟用:"
echo "  - 動態 UI 渲染（iOS 限制模式）"
echo "  - Stars 冷卻期管理（21天）"
echo "  - Magic Link 認證（/web_login）"
echo "  - 反 Sybil 防禦系統"
echo ""
