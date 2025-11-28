# 服務器操作指南

## 🚀 快速更新並重啟

### 方法 1：使用腳本（推薦）

**雙擊運行**：`服務器更新並重啟.bat`

這會自動執行：
1. ✅ 更新代碼
2. ✅ 重啟 API 服務
3. ✅ 檢查服務狀態

---

### 方法 2：手動執行命令

#### 選項 A：從本地執行（SSH）

```bash
ssh ubuntu@165.154.254.99
```

然後在服務器上執行：
```bash
cd /opt/luckyred
git fetch origin
git reset --hard origin/master
sudo systemctl restart luckyred-api
sudo systemctl status luckyred-api
```

#### 選項 B：一行命令（從本地）

```bash
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && sudo systemctl restart luckyred-api"
```

---

## 📋 完整命令列表

### 更新代碼

```bash
cd /opt/luckyred
git fetch origin
git reset --hard origin/master
```

### 重啟服務

```bash
# 重啟 API 服務
sudo systemctl restart luckyred-api

# 重啟 Bot 服務
sudo systemctl restart luckyred-bot

# 重啟 Admin 服務
sudo systemctl restart luckyred-admin

# 重載 Nginx（前端）
sudo systemctl reload nginx
```

### 檢查服務狀態

```bash
# 檢查 API 服務
sudo systemctl status luckyred-api

# 檢查 Bot 服務
sudo systemctl status luckyred-bot

# 檢查所有服務
sudo systemctl status luckyred-api luckyred-bot nginx
```

### 查看服務日誌

```bash
# 查看 API 服務日誌
sudo journalctl -u luckyred-api -f

# 查看 Bot 服務日誌
sudo journalctl -u luckyred-bot -f

# 查看最近 50 行日誌
sudo journalctl -u luckyred-api -n 50
```

---

## 🔍 常見操作

### 1. 只更新代碼（不重啟）

```bash
cd /opt/luckyred
git pull origin master
```

### 2. 只重啟服務（不更新代碼）

```bash
sudo systemctl restart luckyred-api
```

### 3. 更新代碼並重啟所有服務

```bash
cd /opt/luckyred
git fetch origin
git reset --hard origin/master
sudo systemctl restart luckyred-api luckyred-bot
sudo systemctl reload nginx
```

### 4. 查看服務是否運行

```bash
sudo systemctl is-active luckyred-api
sudo systemctl is-active luckyred-bot
sudo systemctl is-active nginx
```

### 5. 停止服務

```bash
sudo systemctl stop luckyred-api
sudo systemctl stop luckyred-bot
```

### 6. 啟動服務

```bash
sudo systemctl start luckyred-api
sudo systemctl start luckyred-bot
```

---

## ⚠️ 故障排除

### 服務無法啟動

```bash
# 查看詳細錯誤
sudo journalctl -u luckyred-api -n 100

# 檢查配置文件
cat /etc/systemd/system/luckyred-api.service

# 檢查 Python 環境
cd /opt/luckyred/api
source .venv/bin/activate
python --version
```

### 代碼未更新

```bash
# 強制重置
cd /opt/luckyred
git fetch origin
git reset --hard origin/master

# 檢查當前版本
git log --oneline -1
```

### 權限問題

```bash
# 檢查文件權限
ls -la /opt/luckyred

# 修復權限（如果需要）
sudo chown -R ubuntu:ubuntu /opt/luckyred
```

---

## 📝 服務配置文件位置

- API 服務：`/etc/systemd/system/luckyred-api.service`
- Bot 服務：`/etc/systemd/system/luckyred-bot.service`
- Admin 服務：`/etc/systemd/system/luckyred-admin.service`
- Nginx 配置：`/etc/nginx/sites-enabled/`

---

## 🎯 最佳實踐

1. **更新前檢查**
   ```bash
   git log --oneline origin/master -5  # 查看遠程最新提交
   ```

2. **更新後驗證**
   ```bash
   git log --oneline -1  # 確認已更新
   sudo systemctl status luckyred-api  # 確認服務運行
   ```

3. **查看日誌**
   ```bash
   sudo journalctl -u luckyred-api -f  # 實時查看日誌
   ```

