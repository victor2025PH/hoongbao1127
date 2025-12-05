#!/bin/bash
# 修复Nginx配置并重启服务
# 在服务器上执行: bash scripts/sh/fix-nginx-and-restart.sh

set -e

PROJECT_DIR="/opt/luckyred"
NGINX_CONF="/etc/nginx/sites-enabled/mini.usdt2026.cc-ssl.conf"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "========================================"
echo "   修复Nginx配置并重启"
echo "========================================"
echo ""

# 1. 拉取最新代码
log_info "[1/4] 拉取最新代码..."
cd "$PROJECT_DIR"
git pull origin master || log_warn "Git pull失败，继续执行..."

# 2. 检查Nginx配置
log_info "[2/4] 检查Nginx配置..."
if grep -q "proxy_pass http://127.0.0.1:8080/api/" "$NGINX_CONF"; then
    log_info "✓ Nginx配置正确（已包含/api前缀）"
elif grep -q "proxy_pass http://127.0.0.1:8080/\$" "$NGINX_CONF"; then
    log_warn "⚠ 需要修复Nginx配置..."
    # 备份原配置
    sudo cp "$NGINX_CONF" "$NGINX_CONF.backup.$(date +%Y%m%d_%H%M%S)"
    # 修复配置
    sudo sed -i 's|proxy_pass http://127.0.0.1:8080/;|proxy_pass http://127.0.0.1:8080/api/;|g' "$NGINX_CONF"
    log_info "✓ Nginx配置已修复"
else
    log_warn "⚠ 无法自动修复，请手动检查Nginx配置"
fi

# 3. 测试Nginx配置
log_info "[3/4] 测试Nginx配置..."
if sudo nginx -t; then
    log_info "✓ Nginx配置测试通过"
else
    log_error "✗ Nginx配置测试失败"
    exit 1
fi

# 4. 重新加载Nginx
log_info "[4/4] 重新加载Nginx..."
sudo systemctl reload nginx
log_info "✓ Nginx已重新加载"

echo ""
echo "========================================"
log_info "修复完成！"
echo "========================================"
echo ""
echo "📋 测试命令："
echo "  curl https://mini.usdt2026.cc/api/v1/tasks/status"
echo "  应该返回 401 (需要认证) 或 JSON 数据"
echo ""

