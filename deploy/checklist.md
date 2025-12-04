# ✅ 部署檢查清單

## 📋 部署前檢查

### 環境準備
- [ ] 服務器操作系統已更新
- [ ] Python 3.10+ 已安裝
- [ ] PostgreSQL 14+ 已安裝並運行
- [ ] Nginx 已安裝
- [ ] Node.js 18+ 已安裝（前端需要）
- [ ] 防火牆已配置（開放 22, 80, 443 端口）

### 項目配置
- [ ] 項目代碼已上傳到 `/opt/luckyred`
- [ ] `.env` 文件已創建並配置
- [ ] 所有必要的環境變量已設置：
  - [ ] `BOT_TOKEN`
  - [ ] `BOT_USERNAME`
  - [ ] `ADMIN_IDS`
  - [ ] `DATABASE_URL`
  - [ ] `JWT_SECRET`
  - [ ] `API_BASE_URL`
  - [ ] 域名配置

### 數據庫
- [ ] PostgreSQL 數據庫已創建
- [ ] 數據庫用戶已創建並有權限
- [ ] 數據庫連接測試通過
- [ ] 數據庫已初始化（表結構已創建）

### Python 環境
- [ ] API 虛擬環境已創建
- [ ] API 依賴已安裝
- [ ] Bot 虛擬環境已創建
- [ ] Bot 依賴已安裝

### Systemd 服務
- [ ] `luckyred-api.service` 已配置
- [ ] `luckyred-bot.service` 已配置
- [ ] 服務文件已複製到 `/etc/systemd/system/`
- [ ] Systemd 已重新加載
- [ ] 服務已啟用（enable）

### Nginx 配置
- [ ] Nginx 配置文件已複製
- [ ] 站點配置已啟用（符號鏈接）
- [ ] Nginx 配置測試通過
- [ ] SSL 證書已配置（生產環境）

### 前端
- [ ] Miniapp 依賴已安裝
- [ ] Miniapp 已構建
- [ ] Admin 依賴已安裝（如需要）
- [ ] Admin 已構建（如需要）

## 🚀 部署後檢查

### 服務狀態
- [ ] API 服務運行正常 (`systemctl status luckyred-api`)
- [ ] Bot 服務運行正常 (`systemctl status luckyred-bot`)
- [ ] Nginx 服務運行正常 (`systemctl status nginx`)
- [ ] PostgreSQL 服務運行正常 (`systemctl status postgresql`)

### 端口檢查
- [ ] API 端口 8080 可訪問
- [ ] HTTP 端口 80 可訪問
- [ ] HTTPS 端口 443 可訪問
- [ ] PostgreSQL 端口 5432 可訪問

### 功能測試
- [ ] API 健康檢查通過 (`curl http://localhost:8080/health`)
- [ ] API 文檔可訪問（如果 DEBUG=true）
- [ ] Bot 響應 `/start` 命令
- [ ] Miniapp 可正常訪問
- [ ] Admin 可正常訪問（如需要）

### 日誌檢查
- [ ] API 日誌無錯誤
- [ ] Bot 日誌無錯誤
- [ ] Nginx 訪問日誌正常
- [ ] Nginx 錯誤日誌無錯誤

### 性能檢查
- [ ] API 響應時間正常
- [ ] 數據庫查詢性能正常
- [ ] 內存使用正常
- [ ] CPU 使用正常

## 🔒 安全檢查

- [ ] 所有密碼已更改為強密碼
- [ ] `.env` 文件權限設置正確（600）
- [ ] SSL 證書有效且自動續期已配置
- [ ] 防火牆規則已配置
- [ ] SSH 訪問已限制
- [ ] 定期備份已設置

## 📊 監控設置

- [ ] 日誌輪轉已配置
- [ ] 備份腳本已設置
- [ ] 定時任務已配置
- [ ] 監控工具已安裝（可選）

## 🎯 完成標記

- [ ] 所有檢查項已完成
- [ ] 系統運行正常
- [ ] 文檔已更新
- [ ] 團隊已通知

---

**部署日期**: _______________
**部署人員**: _______________
**備註**: _______________
