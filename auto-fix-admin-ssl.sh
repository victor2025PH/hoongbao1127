#!/bin/bash
# 全自动修复 admin.usdt2026.cc SSL 配置

set -e

echo "=========================================="
echo "  全自动修复 admin.usdt2026.cc SSL 配置"
echo "=========================================="

APP_DIR="/opt/luckyred"
NGINX_CONF="/etc/nginx/sites-available/admin.usdt2026.cc.conf"
DOMAIN="admin.usdt2026.cc"
EMAIL="admin@usdt2026.cc"

# 1. 更新代码
echo ""
echo "[1/6] 更新代码..."
cd $APP_DIR
git pull origin master || echo "⚠️  git pull 失败，继续执行..."

# 2. 检查 SSL 证书
echo ""
echo "[2/6] 检查 SSL 证书..."
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "✅ SSL 证书已存在"
    HAS_SSL=true
    CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
else
    echo "⚠️  SSL 证书不存在，将自动获取"
    HAS_SSL=false
    CERT_PATH=""
fi

# 3. 如果没有证书，获取证书
if [ "$HAS_SSL" = false ]; then
    echo ""
    echo "[3/6] 获取 SSL 证书..."
    # 确保 HTTP 配置正确（certbot 需要）
    sudo cp $APP_DIR/deploy/nginx/admin.usdt2026.cc.conf $NGINX_CONF
    sudo nginx -t && sudo systemctl reload nginx
    
    # 获取证书
    if sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect 2>&1; then
        echo "✅ SSL 证书获取成功"
        HAS_SSL=true
        CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
    else
        echo "⚠️  SSL 证书获取失败，将使用 HTTP 配置"
        HAS_SSL=false
    fi
else
    echo ""
    echo "[3/6] 跳过证书获取（已存在）"
fi

# 4. 更新 Nginx 配置
echo ""
echo "[4/6] 更新 Nginx 配置..."
if [ "$HAS_SSL" = true ]; then
    echo "使用 SSL 配置..."
    # certbot 应该已经自动更新了配置，但我们需要确保配置正确
    # 检查配置是否包含 HTTPS
    if sudo nginx -T 2>/dev/null | grep -q "server_name $DOMAIN" | grep -q "listen 443"; then
        echo "✅ HTTPS 配置已存在"
    else
        echo "添加 HTTPS 配置..."
        # 备份原配置
        sudo cp $NGINX_CONF $NGINX_CONF.backup.$(date +%Y%m%d_%H%M%S)
        
        # 创建完整的 HTTPS 配置
        sudo tee $NGINX_CONF > /dev/null <<EOF
# Admin 後台 (HTTPS)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $CERT_PATH/fullchain.pem;
    ssl_certificate_key $CERT_PATH/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 管理後台靜態文件
    root /opt/luckyred/admin/frontend/dist;
    index index.html;

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端路由 (SPA)
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # 避免对已存在的文件进行重定向
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 安全頭
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}
EOF
    fi
else
    echo "使用 HTTP 配置..."
    sudo cp $APP_DIR/deploy/nginx/admin.usdt2026.cc.conf $NGINX_CONF
fi

# 5. 确保站点已启用
echo ""
echo "[5/6] 确保站点已启用..."
sudo ln -sf /etc/nginx/sites-available/admin.usdt2026.cc.conf /etc/nginx/sites-enabled/admin.usdt2026.cc.conf

# 6. 测试并重新加载 Nginx
echo ""
echo "[6/6] 测试并重新加载 Nginx..."
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx 配置已更新并重新加载"
else
    echo "❌ Nginx 配置测试失败"
    exit 1
fi

# 7. 验证配置
echo ""
echo "=========================================="
echo "  验证配置"
echo "=========================================="

echo ""
echo "检查服务状态:"
systemctl status luckyred-api --no-pager | head -5 || true

echo ""
echo "检查端口监听:"
sudo netstat -tlnp 2>/dev/null | grep 8080 || echo "⚠️  端口 8080 未监听"

echo ""
echo "检查 Nginx 配置:"
if sudo nginx -T 2>/dev/null | grep -A 5 "server_name $DOMAIN" | grep -q "listen 443"; then
    echo "✅ HTTPS 配置已生效"
    echo "访问：https://$DOMAIN"
else
    echo "⚠️  只有 HTTP 配置"
    echo "访问：http://$DOMAIN"
    echo ""
    echo "如果需要 HTTPS，请手动执行："
    echo "  sudo certbot --nginx -d $DOMAIN"
fi

echo ""
echo "=========================================="
echo "  ✅ 配置完成！"
echo "=========================================="

