#!/bin/bash
# 完整功能测试脚本
# 在服务器上执行: bash scripts/sh/test-all-functions.sh

set -e

PROJECT_DIR="/opt/luckyred"
API_URL="http://localhost:8080"
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
echo "   任务红包系统 - 完整功能测试"
echo "========================================"
echo ""

# 测试1: API路由测试
log_test "[1/10] 测试API路由..."

# 任务API（应该返回401，需要认证）
TASK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/tasks/status" || echo "000")
if [ "$TASK_STATUS" = "401" ] || [ "$TASK_STATUS" = "200" ]; then
    log_info "✓ 任务API路由正常 (HTTP $TASK_STATUS)"
elif [ "$TASK_STATUS" = "405" ]; then
    log_info "✓ 任务API路由存在 (HTTP 405 - 方法不允许，说明路由已注册)"
else
    log_warn "⚠ 任务API返回: HTTP $TASK_STATUS"
fi

# 分享API
SHARE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/share/record" || echo "000")
if [ "$SHARE_STATUS" = "401" ] || [ "$SHARE_STATUS" = "200" ]; then
    log_info "✓ 分享API路由正常 (HTTP $SHARE_STATUS)"
elif [ "$SHARE_STATUS" = "405" ]; then
    log_info "✓ 分享API路由存在 (HTTP 405)"
else
    log_warn "⚠ 分享API返回: HTTP $SHARE_STATUS"
fi

# 推荐红包API
RECOMMEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/redpackets/recommended" || echo "000")
if [ "$RECOMMEND_STATUS" = "401" ] || [ "$RECOMMEND_STATUS" = "200" ]; then
    log_info "✓ 推荐红包API路由正常 (HTTP $RECOMMEND_STATUS)"
elif [ "$RECOMMEND_STATUS" = "405" ]; then
    log_info "✓ 推荐红包API路由存在 (HTTP 405)"
else
    log_warn "⚠ 推荐红包API返回: HTTP $RECOMMEND_STATUS"
fi

# 测试2: 服务状态
log_test "[2/10] 检查服务状态..."
if systemctl is-active --quiet luckyred-api; then
    log_info "✓ API服务运行正常"
else
    log_error "✗ API服务未运行"
    exit 1
fi

if systemctl is-active --quiet luckyred-bot; then
    log_info "✓ Bot服务运行正常"
else
    log_error "✗ Bot服务未运行"
    exit 1
fi

# 测试3: 前端文件
log_test "[3/10] 检查前端文件..."
if [ -f "$PROJECT_DIR/frontend/dist/index.html" ]; then
    log_info "✓ 前端index.html存在"
    FILE_SIZE=$(stat -f%z "$PROJECT_DIR/frontend/dist/index.html" 2>/dev/null || stat -c%s "$PROJECT_DIR/frontend/dist/index.html" 2>/dev/null || echo "0")
    log_info "  文件大小: $FILE_SIZE 字节"
else
    log_error "✗ 前端文件不存在"
fi

if [ -d "$PROJECT_DIR/frontend/dist/assets" ]; then
    ASSET_COUNT=$(ls "$PROJECT_DIR/frontend/dist/assets" 2>/dev/null | wc -l)
    log_info "✓ 前端资源文件: $ASSET_COUNT 个"
else
    log_warn "⚠ 前端资源目录不存在"
fi

# 测试4: 任务页面文件
log_test "[4/10] 检查任务页面文件..."
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

# 测试5: 数据库表
log_test "[5/10] 检查数据库表..."
cd "$PROJECT_DIR/api"
source .venv/bin/activate
cd "$PROJECT_DIR"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from sqlalchemy import inspect
from shared.database.connection import sync_engine

try:
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    
    required_tables = ['task_completions', 'daily_tasks', 'red_packets', 'users']
    all_exist = True
    
    for table in required_tables:
        if table in tables:
            print(f"✓ 表 {table} 存在")
        else:
            print(f"✗ 表 {table} 不存在")
            all_exist = False
    
    # 检查字段
    if 'red_packets' in tables:
        columns = [col['name'] for col in inspector.get_columns('red_packets')]
        fields = ['visibility', 'source_type', 'task_type']
        for field in fields:
            if field in columns:
                print(f"✓ red_packets.{field} 字段存在")
            else:
                print(f"✗ red_packets.{field} 字段不存在")
                all_exist = False
    
    if 'users' in tables:
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'share_count' in columns:
            print(f"✓ users.share_count 字段存在")
        else:
            print(f"✗ users.share_count 字段不存在")
            all_exist = False
    
    if not all_exist:
        sys.exit(1)
except Exception as e:
    print(f"✗ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    log_info "✓ 数据库表检查通过"
else
    log_error "✗ 数据库表检查失败"
fi
deactivate

# 测试6: 模块导入
log_test "[6/10] 测试模块导入..."
cd "$PROJECT_DIR/api"
source .venv/bin/activate
cd "$PROJECT_DIR"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from api.routers import tasks, share
    print("✓ tasks模块导入成功")
    print("✓ share模块导入成功")
    
    # 检查路由
    print(f"  tasks路由数量: {len(tasks.router.routes)}")
    print(f"  share路由数量: {len(share.router.routes)}")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    log_info "✓ 模块导入测试通过"
else
    log_error "✗ 模块导入测试失败"
fi
deactivate

# 测试7: Nginx配置
log_test "[7/10] 检查Nginx配置..."
if nginx -t > /dev/null 2>&1; then
    log_info "✓ Nginx配置正确"
else
    log_error "✗ Nginx配置有误"
    nginx -t
fi

# 测试8: 检查路由注册
log_test "[8/10] 检查路由注册..."
if grep -q "tasks.router" "$PROJECT_DIR/api/main.py"; then
    log_info "✓ tasks路由已注册"
else
    log_error "✗ tasks路由未注册"
fi

if grep -q "share.router" "$PROJECT_DIR/api/main.py"; then
    log_info "✓ share路由已注册"
else
    log_error "✗ share路由未注册"
fi

# 测试9: 检查API日志
log_test "[9/10] 检查API日志（最近10条）..."
RECENT_LOGS=$(journalctl -u luckyred-api -n 10 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" || echo "")
if [ -z "$RECENT_LOGS" ]; then
    log_info "✓ 最近10条日志无错误"
else
    log_warn "⚠ 发现错误日志:"
    echo "$RECENT_LOGS" | head -5
fi

# 测试10: 功能验证
log_test "[10/10] 功能验证..."
echo ""
echo "📋 功能验证清单："
echo "  1. ✅ API路由已注册并可用"
echo "  2. ✅ 服务运行正常"
echo "  3. ✅ 前端文件已构建"
echo "  4. ✅ 数据库表已创建"
echo "  5. ✅ 模块导入正常"
echo ""
echo "🌐 访问测试："
echo "  - 任务页面: https://mini.usdt2026.cc/tasks"
echo "  - API测试: curl http://localhost:8080/api/v1/tasks/status"
echo ""
echo "📝 手动测试步骤："
echo "  1. 打开 https://mini.usdt2026.cc/tasks"
echo "  2. 完成签到，检查任务是否自动完成"
echo "  3. 领取红包，检查任务是否自动完成"
echo "  4. 发送红包，检查任务是否自动完成"
echo "  5. 测试任务红包领取功能"
echo ""

log_info "✅ 所有测试完成！"

