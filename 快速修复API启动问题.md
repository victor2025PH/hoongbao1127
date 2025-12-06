# 🚀 快速修复 API 启动问题

## 🔍 问题诊断

服务仍然无法启动。请执行以下命令查看详细错误：

```bash
# 查看最近 50 行日志
sudo journalctl -u luckyred-api -n 50

# 查看错误信息
sudo journalctl -u luckyred-api | grep -i "error\|exception\|traceback" | tail -20

# 手动测试导入
cd /opt/luckyred/api
source .venv/bin/activate
python3 -c "from api.utils.auth_utils import create_access_token; print('OK')"
python3 -c "from api.main import app; print('OK')"
```

## 🔧 可能的问题和解决方案

### 问题1：`api/utils/__init__.py` 不存在

如果 `api/utils` 目录没有 `__init__.py`，Python 可能无法识别它为包。

**解决方案**：
```bash
# 创建 __init__.py
touch /opt/luckyred/api/utils/__init__.py
```

### 问题2：导入路径错误

**检查**：
```bash
cd /opt/luckyred/api
source .venv/bin/activate
python3 -c "import sys; sys.path.insert(0, '.'); from api.utils.auth_utils import create_access_token; print('OK')"
```

### 问题3：依赖缺失

**检查**：
```bash
cd /opt/luckyred/api
source .venv/bin/activate
pip list | grep -E "jose|pydantic|fastapi"
```

## 🚀 快速修复步骤

```bash
# 1. 确保 api/utils/__init__.py 存在
cd /opt/luckyred/api
touch utils/__init__.py

# 2. 测试导入
source .venv/bin/activate
python3 -c "from api.utils.auth_utils import create_access_token, TokenResponse; print('✅ 导入成功')"

# 3. 测试主应用导入
python3 -c "from api.main import app; print('✅ 主应用导入成功')"

# 4. 如果测试通过，重启服务
sudo systemctl restart luckyred-api

# 5. 等待 5 秒后检查
sleep 5
sudo systemctl status luckyred-api
curl http://localhost:8080/health
```

## 📋 完整诊断命令

```bash
# 运行诊断脚本
cd /opt/luckyred
bash scripts/sh/check-api-errors.sh
```

## ⚠️ 如果仍然失败

请提供完整的错误日志：
```bash
sudo journalctl -u luckyred-api -n 100 --no-pager > /tmp/api-errors.log
cat /tmp/api-errors.log
```

然后将错误信息发送给我，我会进一步诊断。

