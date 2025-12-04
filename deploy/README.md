# 📦 部署文件說明

## 目錄結構

```
deploy/
├── nginx/              # Nginx 配置文件
│   ├── mini.usdt2026.cc.conf
│   └── admin.usdt2026.cc.conf
├── scripts/            # 部署腳本
│   ├── deploy-full.sh  # 完整部署腳本
│   └── quick-update.sh # 快速更新腳本
├── systemd/            # Systemd 服務文件
│   ├── luckyred-api.service
│   ├── luckyred-bot.service
│   └── luckyred-admin.service
└── checklist.md        # 部署檢查清單
```

## 使用說明

### 完整部署
```bash
sudo bash deploy/scripts/deploy-full.sh
```

### 快速更新
```bash
sudo bash deploy/scripts/quick-update.sh
```

### 手動部署
參考 `DEPLOYMENT_GUIDE.md` 進行手動部署。

## 服務文件說明

### API 服務 (`luckyred-api.service`)
- 運行 FastAPI 應用
- 監聽 `127.0.0.1:8080`
- 自動重啟

### Bot 服務 (`luckyred-bot.service`)
- 運行 Telegram Bot
- 使用 polling 模式
- 自動重啟

## Nginx 配置

### Miniapp (`mini.usdt2026.cc.conf`)
- 代理到前端靜態文件
- 反向代理 API 請求到 `127.0.0.1:8080`

### Admin (`admin.usdt2026.cc.conf`)
- 代理到管理後台
- 需要認證（可選）

## 注意事項

1. **環境變量**: 確保 `/opt/luckyred/.env` 文件已正確配置
2. **文件權限**: 確保服務用戶有權限訪問項目目錄
3. **SSL 證書**: 生產環境必須配置 SSL 證書
4. **防火牆**: 確保必要端口已開放

## 故障排除

查看服務日誌：
```bash
sudo journalctl -u luckyred-api -f
sudo journalctl -u luckyred-bot -f
```

檢查服務狀態：
```bash
sudo systemctl status luckyred-api
sudo systemctl status luckyred-bot
```

重啟服務：
```bash
sudo systemctl restart luckyred-api
sudo systemctl restart luckyred-bot
```
