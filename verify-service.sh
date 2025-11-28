#!/bin/bash
# 验证服务状态和连接

set -e

echo "=========================================="
echo "  验证服务状态"
echo "=========================================="

# 1. 检查服务状态
echo ""
echo "[1/5] 检查服务状态..."
systemctl status luckyred-api --no-pager | head -15

# 2. 检查端口监听
echo ""
echo "[2/5] 检查端口监听..."
sudo netstat -tlnp | grep 8080 || echo "⚠️  端口 8080 未监听"

# 3. 测试后端 API
echo ""
echo "[3/5] 测试后端 API..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8080/api/v1/admin/auth/login || echo "❌ 无法连接到后端 API"

# 4. 检查 Nginx 配置
echo ""
echo "[4/5] 检查 Nginx 配置..."
if [ -f "/etc/nginx/sites-available/admin.usdt2026.cc.conf" ]; then
    echo "✅ Nginx 配置文件存在"
    echo "Root 路径:"
    grep "root" /etc/nginx/sites-available/admin.usdt2026.cc.conf | head -1
    echo "Proxy 配置:"
    grep "proxy_pass" /etc/nginx/sites-available/admin.usdt2026.cc.conf | head -1
else
    echo "❌ Nginx 配置文件不存在"
fi

# 5. 检查 Nginx 错误日志
echo ""
echo "[5/5] 检查 Nginx 错误日志（最近 10 行）..."
sudo tail -10 /var/log/nginx/error.log || echo "⚠️  无法读取错误日志"

echo ""
echo "=========================================="
echo "  验证完成"
echo "=========================================="

