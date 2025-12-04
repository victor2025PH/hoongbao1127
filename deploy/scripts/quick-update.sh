#!/bin/bash
# ============================================
# Lucky Red 快速更新腳本
# ============================================

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/opt/luckyred"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 更新代碼
log_info "更新代碼..."
cd "$PROJECT_DIR"
git fetch origin
git reset --hard origin/master
log_info "代碼已更新"

# 更新 API
log_info "更新 API..."
cd "$PROJECT_DIR/api"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt
    deactivate
fi
sudo systemctl restart luckyred-api
log_info "API 已更新並重啟"

# 更新 Bot
log_info "更新 Bot..."
cd "$PROJECT_DIR/bot"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt
    deactivate
fi
sudo systemctl restart luckyred-bot
log_info "Bot 已更新並重啟"

# 更新前端
log_info "更新前端..."
cd "$PROJECT_DIR/frontend"
if [ -f "package.json" ]; then
    npm install
    npm run build
fi
sudo systemctl reload nginx
log_info "前端已更新"

log_info "更新完成！"
