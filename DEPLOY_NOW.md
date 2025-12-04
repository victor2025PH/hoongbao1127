# 🚀 立即開始部署

## 快速開始（3 步）

### 步驟 1: 配置環境變量
```bash
# Windows
copy .env.example .env
notepad .env

# Linux/Mac
cp .env.example .env
nano .env
```

**必須配置的變量：**
- `BOT_TOKEN` - 從 @BotFather 獲取
- `BOT_USERNAME` - Bot 用戶名（不含 @）
- `ADMIN_IDS` - 你的 Telegram ID（逗號分隔）
- `DATABASE_URL` - 數據庫連接字符串
- `JWT_SECRET` - 隨機生成的強密碼
- `API_BASE_URL` - 生產環境使用 HTTPS URL

### 步驟 2: 選擇部署方式

#### 方式 A: 本地開發測試（Windows）
```powershell
# 運行部署啟動腳本
.\start-deployment.ps1

# 或直接運行
.\部署開始.bat
```

#### 方式 B: 部署到 Linux 服務器
```bash
# 1. 上傳代碼到服務器
scp -r . user@server:/opt/luckyred/

# 2. SSH 登錄
ssh user@server

# 3. 運行部署腳本
cd /opt/luckyred
sudo bash deploy/scripts/deploy-full.sh
```

### 步驟 3: 驗證部署

#### 檢查服務
```bash
# Linux 服務器
sudo systemctl status luckyred-api
sudo systemctl status luckyred-bot

# 查看日誌
sudo journalctl -u luckyred-api -f
sudo journalctl -u luckyred-bot -f
```

#### 測試功能
1. 在 Telegram 中發送 `/start` 給 Bot
2. 訪問 Miniapp 域名
3. 檢查 API: `curl http://localhost:8080/health`

## 詳細文檔

- **快速開始**: `QUICK_START_DEPLOY.md`
- **完整指南**: `DEPLOYMENT_GUIDE.md`
- **檢查清單**: `deploy/checklist.md`

## 需要幫助？

1. 檢查 `.env` 文件是否正確配置
2. 查看日誌文件找出錯誤
3. 參考 `DEPLOYMENT_GUIDE.md` 的故障排除部分

---

**準備好了嗎？運行 `.\start-deployment.ps1` 開始！**
