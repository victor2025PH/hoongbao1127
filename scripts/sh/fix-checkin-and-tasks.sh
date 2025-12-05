#!/bin/bash
# 修复签到和任务显示问题
# 在服务器上执行: bash scripts/sh/fix-checkin-and-tasks.sh

set -e

PROJECT_DIR="/opt/luckyred"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd "$PROJECT_DIR"

# 1. 更新代码
log_info "[1/4] 更新代码..."
git pull origin master || git pull origin main
log_info "✓ 代码已更新"

# 2. 重启API服务（加载新代码）
log_info "[2/4] 重启API服务..."
systemctl restart luckyred-api
sleep 5
log_info "✓ API服务已重启"

# 3. 检查服务状态
log_info "[3/4] 检查服务状态..."
if systemctl is-active --quiet luckyred-api; then
    log_info "✓ API服务运行正常"
else
    log_error "✗ API服务启动失败"
    systemctl status luckyred-api --no-pager | head -10
    exit 1
fi

# 4. 测试API
log_info "[4/4] 测试API..."
sleep 2
TASK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/v1/tasks/status || echo "000")
if [ "$TASK_STATUS" = "401" ] || [ "$TASK_STATUS" = "200" ]; then
    log_info "✓ 任务API正常 (HTTP $TASK_STATUS)"
elif [ "$TASK_STATUS" = "405" ]; then
    log_info "✓ 任务API路由存在 (HTTP 405)"
else
    log_warn "⚠ 任务API返回: HTTP $TASK_STATUS"
fi

echo ""
log_info "✅ 修复完成！"
echo ""
echo "📋 测试步骤："
echo "  1. 访问 https://mini.usdt2026.cc/tasks 查看任务列表"
echo "  2. 测试签到功能，检查是否出错"
echo "  3. 检查任务是否显示"
echo ""

