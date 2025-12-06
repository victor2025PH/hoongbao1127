#!/bin/bash
# 🔒 防火墙配置脚本
# 用于配置 Ubuntu UFW 防火墙规则

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 权限运行此脚本"
    exit 1
fi

log_info "开始配置防火墙..."

# 1. 启用 UFW（如果未启用）
if ! ufw status | grep -q "Status: active"; then
    log_info "启用 UFW..."
    ufw --force enable
else
    log_info "UFW 已启用"
fi

# 2. 设置默认策略
log_info "设置默认策略..."
ufw default deny incoming
ufw default allow outgoing

# 3. 允许 SSH（重要！防止锁定）
log_info "允许 SSH (端口 22)..."
ufw allow 22/tcp comment 'SSH'

# 4. 允许 HTTP 和 HTTPS
log_info "允许 HTTP (端口 80)..."
ufw allow 80/tcp comment 'HTTP'

log_info "允许 HTTPS (端口 443)..."
ufw allow 443/tcp comment 'HTTPS'

# 5. 允许 API 端口（如果从外部访问）
# 注意：通常 API 只在内网访问，通过 Nginx 反向代理
# 如果需要直接从外部访问，取消下面的注释
# log_info "允许 API (端口 8080)..."
# ufw allow 8080/tcp comment 'API'

# 6. 限制 SSH 连接（可选，提高安全性）
log_info "限制 SSH 连接速率..."
ufw limit 22/tcp comment 'SSH rate limit'

# 7. 显示规则
log_info "当前防火墙规则："
ufw status numbered

log_info ""
log_info "✅ 防火墙配置完成！"
log_info ""
log_warn "⚠️  重要提示："
log_warn "   1. 确保 SSH 端口 (22) 已正确配置"
log_warn "   2. 如果无法连接，请检查防火墙规则"
log_warn "   3. 可以使用 'ufw status' 查看当前规则"
log_warn "   4. 可以使用 'ufw delete <规则编号>' 删除规则"
log_info ""

