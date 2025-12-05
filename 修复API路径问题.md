# 🔧 修复API路径问题

## 🔍 问题分析

从诊断结果看：
- ✅ 后端API正常（localhost:8080 返回401，正常）
- ❌ 浏览器访问返回404（mini.usdt2026.cc/api/v1/tasks/status）

**问题原因**：可能是Nginx配置或前端API路径问题

## 🚀 修复步骤（在服务器上执行）

### 1. 检查Nginx配置

```bash
# 检查Nginx配置
cat /etc/nginx/sites-enabled/mini.usdt2026.cc-ssl.conf | grep -A 10 "location /api"

# 应该看到：
# location /api/ {
#     proxy_pass http://127.0.0.1:8080/;
#     ...
# }
```

### 2. 检查API代理是否正确

```bash
# 测试Nginx代理
curl -H "Host: mini.usdt2026.cc" http://localhost/api/v1/tasks/status

# 或者直接测试
curl https://mini.usdt2026.cc/api/v1/tasks/status
```

### 3. 检查前端API配置

前端API调用路径：
- baseURL: `/api`
- 调用: `/v1/tasks/status`
- 完整路径: `/api/v1/tasks/status` ✅

### 4. 如果Nginx配置有问题，修复它

```bash
# 检查当前配置
sudo nginx -t

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 重新加载Nginx
sudo systemctl reload nginx
```

## 🔍 诊断命令

```bash
cd /opt/luckyred

# 1. 测试本地API（应该返回401）
curl http://localhost:8080/api/v1/tasks/status

# 2. 测试通过Nginx（应该返回401或404）
curl https://mini.usdt2026.cc/api/v1/tasks/status

# 3. 检查Nginx配置
sudo nginx -t
cat /etc/nginx/sites-enabled/mini.usdt2026.cc-ssl.conf | grep -A 5 "location /api"

# 4. 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log | grep tasks
```

## 🐛 可能的问题和解决方案

### 问题1: Nginx代理路径错误

**检查**：
```bash
grep -A 5 "location /api" /etc/nginx/sites-enabled/mini.usdt2026.cc-ssl.conf
```

**应该看到**：
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8080/;
    ...
}
```

### 问题2: API路由未正确注册

**检查**：
```bash
grep -n "tasks.router" /opt/luckyred/api/main.py
```

### 问题3: 前端API路径错误

前端应该调用：`/api/v1/tasks/status`（有 `/api` 前缀）

检查前端代码：
```bash
grep -r "/v1/tasks" /opt/luckyred/frontend/src/
```

