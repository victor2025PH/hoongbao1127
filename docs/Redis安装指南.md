# Redis 安装指南（Windows）

## 📋 Redis 是什么？

Redis 是一个可选的高性能缓存和消息队列服务，用于：
- 高并发抢红包（10k+并发）
- 余额查询缓存
- 异步任务队列

**重要**：Redis 是可选的！如果未安装，系统会自动回退到数据库模式，所有功能仍然正常工作。

---

## 🪟 Windows 安装 Redis

### 方法1: 使用 WSL (推荐)

如果您有 WSL (Windows Subsystem for Linux)：

```bash
# 在 WSL 中安装
sudo apt update
sudo apt install redis-server

# 启动 Redis
sudo service redis-server start

# 检查状态
redis-cli ping  # 应该返回 PONG
```

### 方法2: 使用 Memurai (Windows 原生)

Memurai 是 Redis 的 Windows 原生替代品：

1. 下载：https://www.memurai.com/get-memurai
2. 安装 Memurai
3. 启动服务（会自动作为 Windows 服务运行）

### 方法3: 使用 Docker

如果您有 Docker Desktop：

```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### 方法4: 使用 Chocolatey

```bash
choco install redis-64
```

---

## ✅ 验证 Redis 安装

```bash
# 测试连接
python -c "import redis; r = redis.Redis(); print(r.ping())"
# 应该输出: True
```

---

## 🚀 使用 Redis（可选）

### 启动 Redis

**WSL:**
```bash
wsl sudo service redis-server start
```

**Memurai:**
- 会自动作为 Windows 服务运行
- 在服务管理器中查看状态

**Docker:**
```bash
docker start redis
```

### 测试 Redis 功能

```bash
# 测试 Redis 抢红包
python scripts/py/test_redis_claim.py
```

---

## ⚠️ 如果没有 Redis

**完全没问题！** 系统会：
- ✅ 自动检测 Redis 不可用
- ✅ 回退到数据库模式
- ✅ 所有功能正常工作
- ⚠️ 只是高并发性能会降低（但仍然可以处理正常流量）

---

## 📝 配置

Redis 配置在代码中：
- 主机: `localhost`
- 端口: `6379`
- 数据库: `0`

如果需要修改，编辑：
- `api/services/ledger_service.py`
- `api/services/redis_claim_service.py`

---

## 🎯 总结

- ✅ Redis 是可选的
- ✅ 未安装时系统正常工作
- ✅ 安装后可以获得更好的性能
- ✅ 推荐使用 WSL 或 Docker 方式安装

