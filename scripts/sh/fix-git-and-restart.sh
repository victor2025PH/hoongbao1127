#!/bin/bash
# 解决Git冲突并重启服务
# 在服务器上执行: bash scripts/sh/fix-git-and-restart.sh

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

# 1. 解决Git冲突
log_info "[1/6] 解决Git冲突..."
git stash
git pull origin master || git pull origin main
git stash pop || true
log_info "✓ Git冲突已解决"

# 2. 检查tasks路由是否注册
log_info "[2/6] 检查路由注册..."
if grep -q "tasks.router" "$PROJECT_DIR/api/main.py"; then
    log_info "✓ tasks路由已注册"
else
    log_error "✗ tasks路由未注册"
    exit 1
fi

# 3. 测试tasks模块导入
log_info "[3/6] 测试tasks模块导入..."
cd "$PROJECT_DIR/api"
source .venv/bin/activate
python3 << EOF
try:
    from api.routers import tasks
    print("✓ tasks模块导入成功")
    print(f"  路由数量: {len(tasks.router.routes)}")
    for route in tasks.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  - {list(route.methods)[0] if route.methods else 'GET'} {route.path}")
except Exception as e:
    print(f"✗ tasks模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

if [ $? -ne 0 ]; then
    log_error "tasks模块导入失败，检查依赖..."
    pip install -q sqlalchemy psycopg2-binary fastapi uvicorn
    log_info "✓ 依赖已安装，请重新运行此脚本"
    exit 1
fi
deactivate

# 4. 停止Bot（解决冲突）
log_info "[4/6] 停止Bot服务（解决冲突）..."
systemctl stop luckyred-bot
sleep 2

# 5. 重启API服务
log_info "[5/6] 重启API服务..."
systemctl restart luckyred-api
sleep 5
log_info "✓ API服务已重启"

# 6. 重启Bot服务
log_info "[6/6] 重启Bot服务..."
systemctl restart luckyred-bot
sleep 3
log_info "✓ Bot服务已重启"

# 检查服务状态
log_info "检查服务状态..."
if systemctl is-active --quiet luckyred-api; then
    log_info "✓ API服务运行正常"
else
    log_error "✗ API服务启动失败"
    systemctl status luckyred-api --no-pager | head -10
    exit 1
fi

if systemctl is-active --quiet luckyred-bot; then
    log_info "✓ Bot服务运行正常"
else
    log_error "✗ Bot服务启动失败"
    systemctl status luckyred-bot --no-pager | head -10
    exit 1
fi

# 测试API路由
log_info "测试API路由..."
sleep 3
TASK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/v1/tasks/status || echo "000")
if [ "$TASK_STATUS" = "401" ] || [ "$TASK_STATUS" = "200" ]; then
    log_info "✓ 任务API路由正常 (HTTP $TASK_STATUS)"
elif [ "$TASK_STATUS" = "404" ]; then
    log_error "✗ 任务API路由仍然返回404"
    log_info "检查API日志..."
    journalctl -u luckyred-api -n 20 --no-pager | grep -i error || true
    log_info "尝试重新加载API..."
    systemctl reload luckyred-api
    sleep 3
    TASK_STATUS2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/v1/tasks/status || echo "000")
    if [ "$TASK_STATUS2" = "401" ] || [ "$TASK_STATUS2" = "200" ]; then
        log_info "✓ 重新加载后路由正常 (HTTP $TASK_STATUS2)"
    else
        log_error "✗ 重新加载后仍然返回 $TASK_STATUS2"
    fi
else
    log_warn "⚠ 任务API返回: HTTP $TASK_STATUS"
fi

echo ""
log_info "✅ 修复完成！"
echo ""
echo "📋 验证步骤："
echo "  1. curl http://localhost:8080/api/v1/tasks/status"
echo "  2. 访问 https://mini.usdt2026.cc/tasks"
echo "  3. 查看日志: sudo journalctl -u luckyred-api -f"
echo ""

