# 🚀 一鍵部署指南

## 服務器信息
- **IP**: 165.154.254.99
- **用戶**: ubuntu
- **密碼**: Along2025!!!

## 部署步驟

### 步驟 1: 打開終端連接服務器

```bash
ssh ubuntu@165.154.254.99
```

輸入密碼: `Along2025!!!`

### 步驟 2: 複製並執行以下命令

```bash
# 一鍵部署命令 - 複製全部並粘貼到終端
cd /tmp && curl -fsSL https://raw.githubusercontent.com/victor2025PH/hoongbao1127/master/server-full-deploy.sh -o deploy.sh && chmod +x deploy.sh && sudo bash deploy.sh
```

---

## 部署完成後

### 訪問地址
- **MiniApp**: https://mini.usdt2026.cc
- **Admin 後台**: https://admin.usdt2026.cc  
- **Bot Webhook**: https://bot.usdt2026.cc

### 查看服務狀態
```bash
sudo systemctl status luckyred-api
sudo systemctl status luckyred-bot
```

### 查看日誌
```bash
sudo journalctl -u luckyred-api -f
sudo journalctl -u luckyred-bot -f
```

---

## Bot Token
已配置: `8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs`

