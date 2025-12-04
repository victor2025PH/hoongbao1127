#!/bin/bash
# ============================================
# Lucky Red 完整部署腳本
# ============================================

set -e  # 遇到錯誤立即退出

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 項目路徑
PROJECT_DIR="/opt/luckyred"
ENV_FILE="$PROJECT_DIR/.env"

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查是否為 root 或 sudo
check_permissions() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "請使用 sudo 運行此腳本"
        exit 1
    fi
}

# 檢查環境變量文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "環境變量文件不存在: $ENV_FILE"
        log_info "請先創建 .env 文件（參考 .env.example）"
        exit 1
    fi
    log_info "環境變量文件檢查通過"
}

# 安裝系統依賴
install_system_dependencies() {
    log_info "安裝系統依賴..."
    apt update
    apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx
    log_info "系統依賴安裝完成"
}

# 配置數據庫
setup_database() {
    log_info "配置數據庫..."
    
    # 讀取數據庫配置
    DB_URL=$(grep DATABASE_URL "$ENV_FILE" | cut -d '=' -f2-)
    DB_NAME=$(echo $DB_URL | grep -oP '/(\w+)$' | cut -d'/' -f2)
    DB_USER=$(echo $DB_URL | grep -oP '://(\w+):' | cut -d':' -f3)
    DB_PASS=$(echo $DB_URL | grep -oP '://\w+:([^@]+)' | cut -d':' -f4)
    
    # 創建數據庫和用戶（如果不存在）
    sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
        CREATE DATABASE $DB_NAME;
    END IF;
END
\$\$;

DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
        ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
        ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
        ALTER ROLE $DB_USER SET timezone TO 'UTC';
        GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
    END IF;
END
\$\$;
EOF
    
    log_info "數據庫配置完成"
}

# 安裝 Python 依賴
install_python_dependencies() {
    log_info "安裝 Python 依賴..."
    
    # API 服務
    if [ -d "$PROJECT_DIR/api" ]; then
        log_info "安裝 API 依賴..."
        cd "$PROJECT_DIR/api"
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        log_info "API 依賴安裝完成"
    fi
    
    # Bot 服務
    if [ -d "$PROJECT_DIR/bot" ]; then
        log_info "安裝 Bot 依賴..."
        cd "$PROJECT_DIR/bot"
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        log_info "Bot 依賴安裝完成"
    fi
}

# 初始化數據庫
init_database() {
    log_info "初始化數據庫..."
    cd "$PROJECT_DIR/api"
    source .venv/bin/activate
    python3 -c "from shared.database.connection import init_db; init_db()" || log_warn "數據庫初始化可能已存在"
    deactivate
    log_info "數據庫初始化完成"
}

# 配置 Systemd 服務
setup_systemd_services() {
    log_info "配置 Systemd 服務..."
    
    # 複製服務文件
    if [ -f "$PROJECT_DIR/deploy/systemd/luckyred-api.service" ]; then
        cp "$PROJECT_DIR/deploy/systemd/luckyred-api.service" /etc/systemd/system/
        log_info "API 服務文件已複製"
    fi
    
    if [ -f "$PROJECT_DIR/deploy/systemd/luckyred-bot.service" ]; then
        cp "$PROJECT_DIR/deploy/systemd/luckyred-bot.service" /etc/systemd/system/
        log_info "Bot 服務文件已複製"
    fi
    
    # 重新加載 systemd
    systemctl daemon-reload
    
    # 啟用服務
    systemctl enable luckyred-api 2>/dev/null || true
    systemctl enable luckyred-bot 2>/dev/null || true
    
    log_info "Systemd 服務配置完成"
}

# 配置 Nginx
setup_nginx() {
    log_info "配置 Nginx..."
    
    # 複製配置文件
    if [ -d "$PROJECT_DIR/deploy/nginx" ]; then
        cp "$PROJECT_DIR/deploy/nginx"/*.conf /etc/nginx/sites-available/
        
        # 創建符號鏈接
        for conf in /etc/nginx/sites-available/*.conf; do
            site=$(basename "$conf")
            if [ ! -L "/etc/nginx/sites-enabled/$site" ]; then
                ln -s "/etc/nginx/sites-available/$site" "/etc/nginx/sites-enabled/"
            fi
        done
    fi
    
    # 測試配置
    if nginx -t; then
        systemctl reload nginx
        log_info "Nginx 配置完成"
    else
        log_error "Nginx 配置測試失敗"
        exit 1
    fi
}

# 構建前端
build_frontend() {
    log_info "構建前端..."
    
    # Miniapp
    if [ -d "$PROJECT_DIR/frontend" ]; then
        cd "$PROJECT_DIR/frontend"
        if [ -f "package.json" ]; then
            npm install
            npm run build
            log_info "Miniapp 構建完成"
        fi
    fi
    
    # Admin
    if [ -d "$PROJECT_DIR/admin" ]; then
        cd "$PROJECT_DIR/admin"
        if [ -f "package.json" ]; then
            npm install
            npm run build
            log_info "Admin 構建完成"
        fi
    fi
}

# 啟動服務
start_services() {
    log_info "啟動服務..."
    
    # 啟動 API
    systemctl restart luckyred-api
    sleep 2
    if systemctl is-active --quiet luckyred-api; then
        log_info "API 服務啟動成功"
    else
        log_error "API 服務啟動失敗"
        journalctl -u luckyred-api -n 20 --no-pager
    fi
    
    # 啟動 Bot
    systemctl restart luckyred-bot
    sleep 2
    if systemctl is-active --quiet luckyred-bot; then
        log_info "Bot 服務啟動成功"
    else
        log_error "Bot 服務啟動失敗"
        journalctl -u luckyred-bot -n 20 --no-pager
    fi
    
    # 重載 Nginx
    systemctl reload nginx
    log_info "Nginx 已重載"
}

# 顯示服務狀態
show_status() {
    log_info "服務狀態："
    echo ""
    systemctl status luckyred-api --no-pager -l || true
    echo ""
    systemctl status luckyred-bot --no-pager -l || true
    echo ""
    systemctl status nginx --no-pager -l || true
}

# 主函數
main() {
    log_info "開始部署 Lucky Red..."
    echo ""
    
    check_permissions
    check_env_file
    
    # 執行部署步驟
    install_system_dependencies
    setup_database
    install_python_dependencies
    init_database
    setup_systemd_services
    setup_nginx
    build_frontend
    start_services
    
    echo ""
    log_info "部署完成！"
    echo ""
    show_status
    echo ""
    log_info "請檢查服務狀態和日誌以確認一切正常"
    log_info "查看日誌: sudo journalctl -u luckyred-api -f"
    log_info "查看日誌: sudo journalctl -u luckyred-bot -f"
}

# 運行主函數
main
