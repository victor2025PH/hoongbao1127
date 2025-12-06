# 🔧 修复 Python 路径问题

## 🔍 问题分析

错误：`ModuleNotFoundError: No module named 'api'`

**原因**：
- 在 `/opt/luckyred/api` 目录下运行时，Python 无法找到 `api` 模块
- Python 需要从项目根目录（`/opt/luckyred`）才能正确导入 `api` 模块

## ✅ 解决方案

### 方案1：从项目根目录运行（推荐）

```bash
# 1. 确保在项目根目录
cd /opt/luckyred

# 2. 激活虚拟环境
source api/.venv/bin/activate

# 3. 测试导入（从根目录）
python3 -c "from api.utils.auth_utils import create_access_token, TokenResponse, UserResponse; print('✅ 导入成功')"

# 4. 测试主应用
python3 -c "from api.main import app; print('✅ 主应用导入成功')"
```

### 方案2：设置 PYTHONPATH

```bash
# 在项目根目录设置 PYTHONPATH
cd /opt/luckyred
export PYTHONPATH=/opt/luckyred:$PYTHONPATH

# 然后测试
cd api
source .venv/bin/activate
python3 -c "from api.utils.auth_utils import create_access_token; print('OK')"
```

### 方案3：检查 systemd 服务配置

systemd 服务应该设置正确的工作目录。检查配置：

```bash
# 查看服务配置
cat /etc/systemd/system/luckyred-api.service
```

**正确的配置应该是**：
```ini
[Service]
WorkingDirectory=/opt/luckyred/api
Environment="PATH=/opt/luckyred/api/.venv/bin"
Environment="PYTHONPATH=/opt/luckyred"
```

## 🚀 快速修复步骤

```bash
# 1. 检查当前服务配置
sudo cat /etc/systemd/system/luckyred-api.service

# 2. 如果 PYTHONPATH 未设置，编辑服务文件
sudo nano /etc/systemd/system/luckyred-api.service

# 3. 在 [Service] 部分添加：
# Environment="PYTHONPATH=/opt/luckyred"

# 4. 重新加载 systemd 配置
sudo systemctl daemon-reload

# 5. 重启服务
sudo systemctl restart luckyred-api

# 6. 检查状态
sleep 5
sudo systemctl status luckyred-api
curl http://localhost:8080/health
```

## 📋 查看详细错误日志

```bash
# 查看最近的错误日志
sudo journalctl -u luckyred-api -n 100 --no-pager | grep -A 20 "Error\|Traceback"
```

## ✅ 验证

成功时应该看到：
- 服务状态：`active (running)`
- 健康检查：`{"status": "healthy", ...}`

