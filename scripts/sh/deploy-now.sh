#!/bin/bash
# 🚀 一键部署脚本
# 使用方法: bash deploy-now.sh

set -e

echo "=========================================="
echo "  🚀 开始部署 LuckyRed"
echo "=========================================="

# 配置
PROJECT_DIR="/opt/luckyred"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    echo "   请修改脚本中的 PROJECT_DIR 变量"
    exit 1
fi

cd "$PROJECT_DIR"

# 1. 拉取最新代码
echo ""
echo "📥 [1/7] 拉取最新代码..."
git stash || true
git pull origin master
echo "✅ 代码更新完成"

# 2. 安装API依赖
echo ""
echo "📦 [2/7] 安装API依赖..."
cd "$PROJECT_DIR/api"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    deactivate
    echo "✅ API依赖安装完成"
else
    echo "⚠️  虚拟环境不存在，跳过API依赖安装"
fi

# 3. 安装Bot依赖
echo ""
echo "📦 [3/7] 安装Bot依赖..."
cd "$PROJECT_DIR/bot"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    deactivate
    echo "✅ Bot依赖安装完成"
else
    echo "⚠️  虚拟环境不存在，跳过Bot依赖安装"
fi

# 4. 构建前端
echo ""
echo "🏗️  [4/7] 构建前端..."
cd "$PROJECT_DIR/frontend"
if [ -f "package.json" ]; then
    npm install --silent
    npm run build
    echo "✅ 前端构建完成"
else
    echo "⚠️  package.json不存在，跳过前端构建"
fi

# 5. 运行数据库迁移（可选，如果需要）
echo ""
echo "🗄️  [5/7] 检查数据库迁移..."
cd "$PROJECT_DIR"
if [ -f "migrations/add_universal_identity_system.py" ]; then
    echo "   跳过迁移（如需运行请手动执行）"
fi

# 6. 重启服务
echo ""
echo "🔄 [6/7] 重启服务..."
if systemctl is-active --quiet luckyred-api; then
    systemctl restart luckyred-api
    echo "✅ API服务已重启"
else
    echo "⚠️  API服务未运行"
fi

if systemctl is-active --quiet luckyred-bot; then
    systemctl restart luckyred-bot
    echo "✅ Bot服务已重启"
else
    echo "⚠️  Bot服务未运行"
fi

if systemctl is-active --quiet luckyred-admin; then
    systemctl restart luckyred-admin
    echo "✅ Admin服务已重启"
else
    echo "ℹ️  Admin服务未配置"
fi

if systemctl is-active --quiet nginx; then
    systemctl reload nginx
    echo "✅ Nginx已重新加载"
else
    echo "⚠️  Nginx未运行"
fi

# 7. 检查服务状态
echo ""
echo "📊 [7/7] 检查服务状态..."
echo ""
echo "--- API服务状态 ---"
systemctl status luckyred-api --no-pager | head -3 || echo "❌ API服务未运行"
echo ""
echo "--- Bot服务状态 ---"
systemctl status luckyred-bot --no-pager | head -3 || echo "❌ Bot服务未运行"
echo ""
echo "--- Nginx状态 ---"
systemctl status nginx --no-pager | head -3 || echo "❌ Nginx未运行"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "📝 查看日志："
echo "   API: journalctl -u luckyred-api -f"
echo "   Bot: journalctl -u luckyred-bot -f"
echo ""

