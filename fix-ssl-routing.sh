#!/bin/bash
# 修复 SSL 路由问题

set -e

echo "=========================================="
echo "  修复 SSL 路由问题"
echo "=========================================="

APP_DIR="/opt/luckyred"

# 1. 检查 admin SSL 证书
echo ""
echo "[1/4] 检查 admin SSL 证书..."
if [ -d "/etc/letsencrypt/live/admin.usdt2026.cc" ]; then
    echo "✅ SSL 证书已存在"
    HAS_SSL=true
else
    echo "⚠️  SSL 证书不存在"
    HAS_SSL=false
fi

# 2. 为 admin 添加 SSL 配置（如果有证书）
if [ "$HAS_SSL" = true ]; then
    echo ""
    echo "[2/4] 为 admin 添加 SSL 配置..."
    NGINX_CONF="/etc/nginx/sites-available/admin.usdt2026.cc.conf"
    sudo tee "$NGINX_CONF" > /dev/null <<'EOF'
# Admin 後台 (HTTPS)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/admin.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 管理後台靜態文件
    root /opt/luckyred/admin/frontend/dist;
    index index.html;

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 前端路由 (SPA)
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # 避免对已存在的文件进行重定向
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
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
    server_name admin.usdt2026.cc;
    return 301 https://$server_name$request_uri;
}
EOF
    echo "✅ SSL 配置已添加"
else
    echo ""
    echo "[2/4] 跳过 SSL 配置（证书不存在）"
fi

# 3. 检查并修复 bot 配置，确保不是默认服务器
echo ""
echo "[3/4] 检查 bot 配置..."
BOT_CONF="/etc/nginx/sites-available/bot.usdt2026.cc.conf"
if [ -f "$BOT_CONF" ]; then
    # 检查是否有 default_server
    if grep -q "default_server" "$BOT_CONF"; then
        echo "⚠️  bot.usdt2026.cc 是默认服务器，移除 default_server..."
        sudo sed -i 's/ default_server//g' "$BOT_CONF"
        echo "✅ 已移除 default_server"
    else
        echo "✅ bot.usdt2026.cc 不是默认服务器"
    fi
else
    echo "⚠️  bot.usdt2026.cc 配置文件不存在"
fi

# 4. 添加默认 SSL server 块，拒绝未匹配的 HTTPS 请求
echo ""
echo "[4/4] 添加默认 SSL server 块..."
# 检查是否已有默认 SSL server
if ! sudo nginx -T 2>/dev/null | grep -q "listen 443.*default_server"; then
    echo "添加默认 SSL server 块到 nginx.conf..."
    # 在 http 块中添加默认 SSL server
    sudo tee -a /etc/nginx/nginx.conf > /dev/null <<'EOF'

# 默认 SSL server - 拒绝未匹配的 HTTPS 请求
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;
    
    ssl_certificate /etc/letsencrypt/live/mini.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mini.usdt2026.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    return 444;  # 关闭连接，不返回响应
}
EOF
    echo "✅ 默认 SSL server 已添加"
else
    echo "✅ 默认 SSL server 已存在"
fi

# 5. 测试并重新加载 Nginx
echo ""
echo "测试并重新加载 Nginx..."
sudo nginx -t && sudo systemctl reload nginx
echo "✅ Nginx 配置已更新"

echo ""
echo "=========================================="
echo "  修复完成"
echo "=========================================="
echo ""
if [ "$HAS_SSL" = true ]; then
    echo "✅ admin.usdt2026.cc 已配置 SSL"
    echo "访问：https://admin.usdt2026.cc"
else
    echo "⚠️  admin.usdt2026.cc 没有 SSL 证书"
    echo "请执行：sudo certbot --nginx -d admin.usdt2026.cc"
    echo ""
    echo "或者暂时通过 HTTP 访问："
    echo "  http://admin.usdt2026.cc"
fi

