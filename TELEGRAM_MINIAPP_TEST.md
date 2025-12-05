# 📱 Telegram MiniApp 真機測試指南

## 前置條件

1. ✅ 後端 API 運行中 (`https://api.usdt2026.cc`)
2. ✅ 前端已部署到服務器
3. ✅ Telegram Bot 已創建

---

## 步驟 1：配置 BotFather

### 1.1 設置 MiniApp URL

在 Telegram 中找到 @BotFather，發送以下命令：

```
/mybots
```

選擇您的 Bot，然後：

1. 點擊 **Bot Settings**
2. 點擊 **Menu Button**
3. 點擊 **Configure menu button**
4. 輸入 MiniApp 的 URL：

```
https://usdt2026.cc
```

5. 輸入按鈕文字：

```
🧧 打開紅包
```

### 1.2 設置 Web App

1. 返回 Bot Settings
2. 點擊 **Configure Web App**
3. 點擊 **Edit Web App URL**
4. 輸入：

```
https://usdt2026.cc
```

---

## 步驟 2：測試環境變量

確保服務器上的 `.env` 包含：

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username

# MiniApp Domain
MINIAPP_DOMAIN=usdt2026.cc
MINIAPP_URL=https://usdt2026.cc

# API Domain
API_URL=https://api.usdt2026.cc
```

---

## 步驟 3：開始測試

### 3.1 打開 Bot

1. 在 Telegram 中搜索您的 Bot
2. 點擊 **START** 或發送 `/start`
3. 點擊底部的 **🧧 打開紅包** 按鈕

### 3.2 測試功能清單

#### 基礎功能
- [ ] MiniApp 正常加載
- [ ] 用戶身份識別正確
- [ ] 餘額顯示正確

#### 紅包功能
- [ ] 查看紅包列表
- [ ] 發送紅包
- [ ] 領取紅包
- [ ] 紅包到賬通知

#### 錢包功能
- [ ] 查看餘額
- [ ] 充值頁面
- [ ] 提現頁面
- [ ] 兌換功能

#### 邀請功能
- [ ] 顯示邀請碼
- [ ] 複製邀請碼
- [ ] 分享邀請鏈接

#### 簽到功能
- [ ] 每日簽到
- [ ] 簽到獎勵到賬

---

## 步驟 4：調試技巧

### 4.1 查看控制台日誌

在 Telegram Desktop 版本中：
1. 打開 MiniApp
2. 右鍵點擊頁面
3. 選擇 **Inspect Element**
4. 查看 Console 標籤

### 4.2 查看服務器日誌

```bash
ssh ubuntu@165.154.254.99
sudo journalctl -u luckyred-api -f
```

### 4.3 測試 API 連通性

```bash
curl -s https://api.usdt2026.cc/health | python3 -m json.tool
```

---

## 常見問題

### Q: MiniApp 白屏

**原因**: 前端未正確部署或 CORS 錯誤

**解決**:
```bash
# 檢查前端文件
ls -la /opt/luckyred/frontend/dist/

# 檢查 Nginx 配置
sudo nginx -t
sudo systemctl reload nginx
```

### Q: 用戶未識別

**原因**: initData 驗證失敗

**解決**:
1. 檢查 BOT_TOKEN 是否正確
2. 查看 API 日誌中的錯誤信息

### Q: WebSocket 連接失敗

**原因**: 可能是 Nginx 未配置 WebSocket 代理

**解決**:
在 Nginx 配置中添加：
```nginx
location /ws {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

## 測試帳號

- **測試用戶 Telegram ID**: 5433982810
- **API Key**: test-key-2024

---

## 聯繫支持

如遇到問題，請檢查：
1. 服務器日誌
2. 瀏覽器控制台
3. 網絡請求（F12 -> Network）

