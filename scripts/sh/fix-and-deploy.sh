#!/bin/bash
# 修复依赖并完成部署
# 在服务器上执行: bash scripts/sh/fix-and-deploy.sh

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

# 1. 确保API虚拟环境存在
log_info "[1/7] 检查API虚拟环境..."
cd "$PROJECT_DIR/api"
if [ ! -d ".venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2. 安装依赖
log_info "[2/7] 安装API依赖..."
if [ -f "requirements.txt" ]; then
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    log_info "✓ 依赖已安装"
else
    log_warn "⚠ requirements.txt 不存在，安装基础依赖..."
    pip install -q sqlalchemy psycopg2-binary fastapi uvicorn
fi

# 3. 运行数据库迁移
log_info "[3/7] 运行数据库迁移..."
cd "$PROJECT_DIR"
python3 migrations/add_task_redpacket_system.py
deactivate
log_info "✓ 数据库迁移完成"

# 4. 构建前端
log_info "[4/7] 构建前端..."
cd "$PROJECT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install --silent
fi
npm run build
log_info "✓ 前端构建完成"

# 5. 重启服务
log_info "[5/7] 重启服务..."
systemctl restart luckyred-api
systemctl restart luckyred-bot
sleep 3
log_info "✓ 服务已重启"

# 6. 检查服务状态
log_info "[6/7] 检查服务状态..."
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

# 7. 运行测试
log_info "[7/7] 运行功能测试..."
cd "$PROJECT_DIR/api"
source .venv/bin/activate
cd "$PROJECT_DIR"
python3 scripts/py/test_tasks_api.py
deactivate

echo ""
log_info "✅ 部署完成！"
echo ""
echo "📋 下一步："
echo "  1. 访问 https://mini.usdt2026.cc/tasks 查看任务页面"
echo "  2. 测试签到、抢红包等功能"
echo ""

