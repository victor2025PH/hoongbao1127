# Lucky Red 管理后台

统一管理后台，整合 Telegram Bot、MiniApp 和后台管理功能。

## 🚀 快速开始

### 1. 初始化数据库

```bash
# 初始化数据库表（包括新增的管理后台表）
python -c "from shared.database.connection import init_db; init_db()"
```

### 2. 创建管理员账户

```bash
# 使用脚本创建管理员
python scripts/create_admin_user.py --username admin --password your_password --email admin@example.com
```

### 3. 安装后端依赖

```bash
cd api
pip install -r requirements.txt
```

### 4. 启动后端服务

```bash
cd api
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 5. 安装前端依赖

```bash
cd admin/frontend
npm install
```

### 6. 启动前端开发服务器

```bash
cd admin/frontend
npm run dev
```

前端将在 `http://localhost:3001` 启动

## 📋 功能清单

### 1. 仪表盘
- 用户统计（总数、今日新增）
- 红包统计（总数、进行中）
- 交易统计（总数、总金额）

### 2. 用户管理
- 用户列表（支持搜索）
- Telegram ID 显示和复制
- 用户详情查看
- 余额充值/扣款
- 发送 Telegram 消息

### 3. Telegram 管理
- 群组列表和管理
- 群组 ID 显示和复制
- Bot 状态监控
- 消息发送（单用户/批量）
- 消息记录查看
- ID 解析工具（用户名/链接 → ID）

### 4. 报表管理
- 生成报表（用户/交易/红包/群组）
- 导出格式（Excel/CSV/PDF/JSON）
- 报表下载和历史记录

## 🔐 认证

管理后台使用 JWT Token 认证，登录后 Token 会保存在 localStorage。

## 📊 数据库

所有数据统一使用 `shared/database`，Bot、MiniApp、后台数据完全互通。

## 🛠️ 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL/SQLite
- **前端**: React 18 + TypeScript + Vite + Ant Design 5
- **状态管理**: Zustand
- **数据请求**: React Query (TanStack Query)
- **认证**: JWT + RBAC

## 📝 API 端点

### 认证
- `POST /api/v1/admin/auth/login` - 登录
- `GET /api/v1/admin/auth/me` - 获取当前用户信息

### 仪表盘
- `GET /api/v1/admin/dashboard/stats` - 获取统计数据

### Telegram 管理
- `POST /api/v1/admin/telegram/send-message` - 发送消息
- `POST /api/v1/admin/telegram/send-batch` - 批量发送
- `GET /api/v1/admin/telegram/groups` - 群组列表
- `GET /api/v1/admin/telegram/groups/{chat_id}` - 群组详情
- `GET /api/v1/admin/telegram/messages` - 消息记录
- `POST /api/v1/admin/telegram/resolve-id` - ID 解析

### 报表
- `POST /api/v1/admin/reports/generate` - 生成报表
- `GET /api/v1/admin/reports` - 报表列表
- `GET /api/v1/admin/reports/{report_id}/download` - 下载报表

## 🔧 环境变量

确保 `.env` 文件包含：
- `BOT_TOKEN` - Telegram Bot Token
- `DATABASE_URL` - 数据库连接字符串
- `JWT_SECRET` - JWT 密钥（用于认证）

## 📦 部署

### 前端构建

```bash
cd admin/frontend
npm run build
```

构建产物在 `admin/frontend/dist` 目录

### Nginx 配置

参考 `deploy/nginx/admin.usdt2026.cc.conf`

## 🐛 故障排除

1. **登录失败**: 检查管理员账户是否已创建
2. **API 错误**: 检查后端服务是否运行
3. **数据库错误**: 检查数据库连接和表是否已创建

