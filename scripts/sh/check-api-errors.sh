#!/bin/bash
# 🔍 检查 API 服务错误日志

echo "=========================================="
echo "  🔍 检查 API 服务错误"
echo "=========================================="
echo ""

# 查看最近 50 行日志
echo "📋 最近 50 行日志："
echo "----------------------------------------"
sudo journalctl -u luckyred-api -n 50 --no-pager
echo ""

# 查看错误信息
echo "❌ 错误信息："
echo "----------------------------------------"
sudo journalctl -u luckyred-api --no-pager | grep -i "error\|exception\|traceback" | tail -20
echo ""

# 尝试手动启动测试
echo "🧪 尝试手动启动测试："
echo "----------------------------------------"
cd /opt/luckyred/api
source .venv/bin/activate
python3 -c "from api.main import app; print('✅ 导入成功')" 2>&1 | head -30

