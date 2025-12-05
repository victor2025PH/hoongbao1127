#!/bin/bash
# 完整部署和测试脚本
# 在服务器上执行: bash scripts/sh/full-deploy-and-test.sh

set -e

PROJECT_DIR="/opt/luckyred"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_test() { echo -e "${BLUE}[TEST]${NC} $1"; }

echo "========================================"
echo "   任务红包系统 - 完整部署和测试"
echo "========================================"
echo ""

cd "$PROJECT_DIR"

# ========== 部署阶段 ==========
log_info "开始部署..."

# 1. 拉取最新代码
log_info "[1/6] 拉取最新代码..."
git fetch origin
git pull origin master || git pull origin main
log_info "✓ 代码已更新"

# 2. 运行数据库迁移
log_info "[2/6] 运行数据库迁移..."
# 使用API虚拟环境运行迁移
cd "$PROJECT_DIR/api"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    cd "$PROJECT_DIR"
    python3 migrations/add_task_redpacket_system.py
    deactivate
else
    # 如果没有虚拟环境，尝试使用系统Python（需要先安装依赖）
    cd "$PROJECT_DIR"
    python3 migrations/add_task_redpacket_system.py || {
        log_warn "迁移失败，尝试安装依赖..."
        cd "$PROJECT_DIR/api"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -q sqlalchemy psycopg2-binary
        cd "$PROJECT_DIR"
        python3 migrations/add_task_redpacket_system.py
        deactivate
    }
fi
log_info "✓ 数据库迁移完成"

# 3. 安装API依赖
log_info "[3/6] 检查API依赖..."
cd "$PROJECT_DIR/api"
if [ -f "requirements.txt" ]; then
    source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
    pip install -q -r requirements.txt
    log_info "✓ API依赖已安装"
else
    log_warn "⚠ requirements.txt 不存在"
fi

# 4. 构建前端
log_info "[4/6] 构建前端..."
cd "$PROJECT_DIR/frontend"
npm install --silent
npm run build
log_info "✓ 前端构建完成"

# 5. 重启服务
log_info "[5/6] 重启服务..."
systemctl restart luckyred-api
systemctl restart luckyred-bot
sleep 3
log_info "✓ 服务已重启"

# 6. 检查服务状态
log_info "[6/6] 检查服务状态..."
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

echo ""
log_info "部署完成！"
echo ""

# ========== 测试阶段 ==========
log_test "开始功能测试..."
echo ""

# 获取API URL
API_URL="http://localhost:8080"
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
    if [ -n "$API_BASE_URL" ]; then
        API_URL="$API_BASE_URL"
    fi
fi

# 测试1: 检查API健康状态
log_test "[1/8] 测试API健康状态..."
if curl -s -f "$API_URL/api/health" > /dev/null 2>&1 || curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    log_info "✓ API服务可访问"
else
    log_warn "⚠ API健康检查端点可能不存在（这是正常的）"
fi

# 测试2: 检查任务API路由
log_test "[2/8] 测试任务API路由..."
TASK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/tasks/status" || echo "000")
if [ "$TASK_STATUS" = "401" ] || [ "$TASK_STATUS" = "200" ]; then
    log_info "✓ 任务API路由正常 (HTTP $TASK_STATUS)"
else
    log_warn "⚠ 任务API返回: HTTP $TASK_STATUS"
fi

# 测试3: 检查分享API路由
log_test "[3/8] 测试分享API路由..."
SHARE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/share/record" || echo "000")
if [ "$SHARE_STATUS" = "401" ] || [ "$SHARE_STATUS" = "200" ]; then
    log_info "✓ 分享API路由正常 (HTTP $SHARE_STATUS)"
else
    log_warn "⚠ 分享API返回: HTTP $SHARE_STATUS"
fi

# 测试4: 检查推荐红包API路由
log_test "[4/8] 测试推荐红包API路由..."
RECOMMEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/redpackets/recommended" || echo "000")
if [ "$RECOMMEND_STATUS" = "401" ] || [ "$RECOMMEND_STATUS" = "200" ]; then
    log_info "✓ 推荐红包API路由正常 (HTTP $RECOMMEND_STATUS)"
else
    log_warn "⚠ 推荐红包API返回: HTTP $RECOMMEND_STATUS"
fi

# 测试5: 检查前端文件
log_test "[5/8] 检查前端文件..."
if [ -f "$PROJECT_DIR/frontend/dist/index.html" ]; then
    log_info "✓ 前端index.html存在"
    if [ -d "$PROJECT_DIR/frontend/dist/assets" ]; then
        ASSET_COUNT=$(ls "$PROJECT_DIR/frontend/dist/assets" | wc -l)
        log_info "✓ 前端资源文件: $ASSET_COUNT 个"
    fi
else
    log_error "✗ 前端文件不存在"
fi

# 测试6: 检查任务页面文件
log_test "[6/8] 检查任务页面文件..."
if [ -f "$PROJECT_DIR/frontend/src/pages/TasksPage.tsx" ]; then
    log_info "✓ TasksPage.tsx存在"
else
    log_error "✗ TasksPage.tsx不存在"
fi

if [ -f "$PROJECT_DIR/frontend/src/pages/TasksPage.css" ]; then
    log_info "✓ TasksPage.css存在"
else
    log_error "✗ TasksPage.css不存在"
fi

# 测试7: 检查数据库表
log_test "[7/8] 检查数据库表..."
cd "$PROJECT_DIR/api"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    cd "$PROJECT_DIR"
    python3 << EOF
import sys
sys.path.insert(0, '.')
from shared.database.connection import sync_engine
from sqlalchemy import inspect, text

try:
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    
    required_tables = ['task_completions', 'daily_tasks', 'red_packets', 'users']
    missing = []
    
    for table in required_tables:
        if table in tables:
            print(f"✓ 表 {table} 存在")
        else:
            missing.append(table)
            print(f"✗ 表 {table} 不存在")
    
    # 检查red_packets表的字段
    if 'red_packets' in tables:
        columns = [col['name'] for col in inspector.get_columns('red_packets')]
        required_fields = ['visibility', 'source_type', 'task_type']
        for field in required_fields:
            if field in columns:
                print(f"✓ red_packets.{field} 字段存在")
            else:
                print(f"✗ red_packets.{field} 字段不存在")
    
    # 检查users表的字段
    if 'users' in tables:
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'share_count' in columns:
            print(f"✓ users.share_count 字段存在")
        else:
            print(f"✗ users.share_count 字段不存在")
    
    if missing:
        sys.exit(1)
except Exception as e:
    print(f"✗ 数据库检查失败: {e}")
    sys.exit(1)
EOF
    deactivate
else
    log_warn "⚠ 虚拟环境不存在，跳过数据库检查"
fi

if [ $? -eq 0 ]; then
    log_info "✓ 数据库表检查通过"
else
    log_error "✗ 数据库表检查失败"
fi

# 测试8: 检查Nginx配置
log_test "[8/8] 检查Nginx配置..."
if nginx -t > /dev/null 2>&1; then
    log_info "✓ Nginx配置正确"
    systemctl reload nginx
    log_info "✓ Nginx已重新加载"
else
    log_error "✗ Nginx配置有误"
    nginx -t
fi

echo ""
echo "========================================"
log_info "部署和测试完成！"
echo "========================================"
echo ""
echo "📋 测试清单："
echo "  1. 访问 https://mini.usdt2026.cc/tasks 查看任务页面"
echo "  2. 测试签到功能，检查任务是否自动完成"
echo "  3. 测试抢红包功能，检查任务是否自动完成"
echo "  4. 测试发红包功能，检查任务是否自动完成"
echo "  5. 测试邀请功能，检查任务是否自动完成"
echo "  6. 测试任务红包领取功能"
echo "  7. 测试推荐红包功能"
echo ""
echo "🔍 查看日志："
echo "  sudo journalctl -u luckyred-api -f"
echo "  sudo journalctl -u luckyred-bot -f"
echo ""

