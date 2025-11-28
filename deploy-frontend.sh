#!/bin/bash
# 前端部署脚本

echo "=========================================="
echo "  部署前端更新"
echo "=========================================="

cd /opt/luckyred

echo "[1/4] 拉取最新代码..."
git pull origin master

echo "[2/4] 清理旧的构建文件..."
cd frontend
rm -rf dist
rm -rf node_modules/.vite

echo "[3/4] 重新构建前端..."
npm run build

echo "[4/4] 检查构建结果..."
if [ -f "dist/index.html" ]; then
    echo "✅ 构建成功！"
    ls -lh dist/index.html
else
    echo "❌ 构建失败！"
    exit 1
fi

echo "=========================================="
echo "  部署完成"
echo "=========================================="

