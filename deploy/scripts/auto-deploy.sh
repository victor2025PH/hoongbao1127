#!/bin/bash
# ============================================
# LuckyRed 全自動部署腳本（服務器端）
# ============================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/opt/luckyred"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# 開始部署
log_step "LuckyRed 全自動部署"

# 1. 更新代碼
log_step "步驟 1: 更新代碼"
cd "$PROJECT_DIR"
log_info "當前目錄: $(pwd)"
log_info "拉取最新代碼..."
git fetch origin
if git diff --quiet HEAD origin/master; then
    log_warn "本地代碼已是最新，無需更新"
else
    log_info "發現新代碼，正在更新..."
    git reset --hard origin/master
    log_info "✓ 代碼已更新"
fi

# 2. 構建前端
log_step "步驟 2: 構建前端"
cd "$PROJECT_DIR/frontend"
log_info "安裝依賴..."
npm install --silent 2>&1 | tail -3
log_info "構建前端..."
npm run build 2>&1 | tail -10
log_info "✓ 前端構建完成"

# 3. 重啟服務
log_step "步驟 3: 重啟服務"
log_info "重啟 API..."
sudo systemctl restart luckyred-api
sleep 1
log_info "重啟 Bot..."
sudo systemctl restart luckyred-bot
sleep 1
log_info "重啟 Admin..."
sudo systemctl restart luckyred-admin
sleep 1
log_info "✓ 所有服務已重啟"

# 4. 檢查服務狀態
log_step "步驟 4: 檢查服務狀態"

check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        log_info "✓ $service 運行正常"
        return 0
    else
        log_error "✗ $service 未運行"
        return 1
    fi
}

echo ""
log_info "檢查服務狀態..."
check_service luckyred-api
check_service luckyred-bot
check_service luckyred-admin

# 5. 顯示詳細狀態
log_step "步驟 5: 服務詳細狀態"

echo ""
log_info "API 服務狀態:"
sudo systemctl status luckyred-api --no-pager | head -10

echo ""
log_info "Bot 服務狀態:"
sudo systemctl status luckyred-bot --no-pager | head -10

echo ""
log_info "Admin 服務狀態:"
sudo systemctl status luckyred-admin --no-pager | head -10

# 完成
log_step "部署完成！"
echo ""
log_info "MiniApp: https://mini.usdt2026.cc"
log_info "Admin: https://admin.usdt2026.cc"
echo ""
log_info "請訪問網站確認部署是否成功"
log_info "特別檢查遊戲規則彈窗功能"
echo ""
