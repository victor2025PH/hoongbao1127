# 🔧 服务器 Git Pull 冲突解决方案

## ❌ 当前问题

执行 `git pull origin master` 时遇到错误：

```
error: Your local changes to the following files would be overwritten by merge:
    frontend/src/App.tsx
    frontend/src/pages/EarnPage.tsx
    frontend/src/pages/SendRedPacket.tsx
    frontend/src/pages/WalletPage.tsx
    frontend/src/utils/api.ts
Please commit your changes or stash them before you merge.
Aborting
```

**原因**：服务器上有本地未提交的更改，Git 无法自动合并。

---

## ✅ 解决方案

### 方案1：自动处理（推荐）

使用改进后的部署脚本，它会自动处理本地更改：

```bash
cd /opt/luckyred
bash scripts/sh/pull-and-deploy.sh
```

**脚本会自动**：
1. 检测本地更改
2. 自动 stash 本地更改
3. 拉取最新代码
4. 如果失败，会重置到远程分支状态

### 方案2：手动 Stash 后拉取

```bash
cd /opt/luckyred

# 1. 保存本地更改
git stash save "服务器本地更改 $(date '+%Y-%m-%d %H:%M:%S')"

# 2. 拉取最新代码
git pull origin master

# 3. 如果需要恢复本地更改（通常不需要）
# git stash pop
```

### 方案3：强制重置到远程分支（丢弃本地更改）

**⚠️ 警告**：这会丢失所有本地未提交的更改！

```bash
cd /opt/luckyred

# 1. 查看本地更改（可选，确认要丢弃的内容）
git status

# 2. 强制重置到远程分支
git fetch origin master
git reset --hard origin/master

# 3. 清理未跟踪的文件（可选）
git clean -fd
```

### 方案4：提交本地更改后拉取

如果本地更改需要保留：

```bash
cd /opt/luckyred

# 1. 提交本地更改
git add -A
git commit -m "服务器本地更改"

# 2. 拉取最新代码（可能会有合并冲突）
git pull origin master

# 3. 如果有冲突，解决冲突后
git add -A
git commit -m "解决合并冲突"
```

---

## 🚀 完整操作流程

### 步骤1：处理 Git 冲突

```bash
# SSH 连接
ssh ubuntu@your-server-ip

# 进入项目目录
cd /opt/luckyred

# 方法A：自动 stash（推荐）
git stash
git pull origin master

# 方法B：强制重置（如果不需要本地更改）
git fetch origin master
git reset --hard origin/master
```

### 步骤2：执行部署

```bash
# 如果脚本已存在
bash scripts/sh/pull-and-deploy.sh

# 如果脚本不存在，手动执行
cd /opt/luckyred

# 安装 API 依赖
cd api
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 安装 Bot 依赖
cd bot
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 构建前端
cd frontend
npm install
npm run build
cd ..

# 重启服务
sudo systemctl restart luckyred-api
sudo systemctl restart luckyred-bot
sudo systemctl reload nginx
```

---

## 📋 快速命令（复制粘贴）

### 一键解决并部署

```bash
cd /opt/luckyred && \
git stash && \
git pull origin master && \
bash scripts/sh/pull-and-deploy.sh
```

### 如果脚本不存在，强制拉取后手动部署

```bash
cd /opt/luckyred && \
git fetch origin master && \
git reset --hard origin/master && \
bash scripts/sh/pull-and-deploy.sh
```

---

## 🔍 诊断命令

### 检查本地更改

```bash
cd /opt/luckyred
git status
git diff
```

### 查看 Stash 列表

```bash
git stash list
```

### 恢复 Stash（如果需要）

```bash
# 查看 stash 内容
git stash show -p stash@{0}

# 恢复 stash
git stash pop

# 或应用但不删除
git stash apply stash@{0}
```

---

## ⚠️ 注意事项

1. **Stash vs Reset**
   - `git stash`：保存本地更改，可以恢复
   - `git reset --hard`：永久丢弃本地更改，无法恢复

2. **生产环境建议**
   - 生产服务器上通常不应该有本地未提交的更改
   - 建议使用 `git reset --hard origin/master` 强制同步到远程状态

3. **备份重要更改**
   - 如果本地有重要更改，先备份：
   ```bash
   cp -r /opt/luckyred /opt/luckyred-backup-$(date +%Y%m%d)
   ```

---

## 🎯 推荐做法

**生产服务器部署流程**：

```bash
# 1. 进入项目目录
cd /opt/luckyred

# 2. 强制同步到远程（丢弃所有本地更改）
git fetch origin master
git reset --hard origin/master

# 3. 执行部署脚本
bash scripts/sh/pull-and-deploy.sh
```

这样可以确保服务器代码始终与 GitHub 仓库保持一致。

