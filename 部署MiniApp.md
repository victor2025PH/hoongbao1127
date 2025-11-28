# MiniApp 部署指南

## 本地代碼已提交

所有更改已提交並推送到遠程倉庫。

## 服務器部署步驟

### 方法 1: 使用自動部署腳本（推薦）

1. 將 `deploy-miniapp.sh` 上傳到服務器
2. 在服務器上執行：
```bash
chmod +x deploy-miniapp.sh
./deploy-miniapp.sh
```

### 方法 2: 手動部署

在服務器上執行以下命令：

```bash
# 1. 進入項目目錄
cd /opt/luckyred

# 2. 拉取最新代碼
git pull origin master

# 3. 更新 Bot Token（如果需要）
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env

# 4. 重啟 API 服務
sudo systemctl restart luckyred-api
sudo systemctl status luckyred-api --no-pager

# 5. 重啟 Bot 服務
sudo systemctl restart luckyred-bot
sudo systemctl status luckyred-bot --no-pager

# 6. 構建前端
cd frontend
sudo rm -rf dist
npm run build

# 7. 重載 Nginx
sudo systemctl reload nginx
```

## 本次更新內容

### 1. Bot Token 更新
- 新 Token: `8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs`

### 2. 群組搜索功能
- ✅ 支持基於鏈接的群組搜索（`t.me/xxx`）
- ✅ 統一搜索接口，同時搜索群組和用戶
- ✅ 智能驗證用戶是否在群組中
- ✅ 個人用戶可以使用搜索功能

### 3. 紅包發送改進
- ✅ 自動嘗試發送消息到群組
- ✅ 如果機器人不在群組中，提供分享鏈接
- ✅ 用戶可以手動分享紅包到群組

### 4. 用戶體驗優化
- ✅ 更友好的錯誤提示
- ✅ 多語言支持完善
- ✅ 智能引導用戶加入群組或分享鏈接

## 驗證部署

### 1. 檢查服務狀態
```bash
sudo systemctl status luckyred-bot --no-pager
sudo systemctl status luckyred-api --no-pager
sudo systemctl status nginx --no-pager
```

### 2. 檢查日誌
```bash
# Bot 日誌
sudo journalctl -u luckyred-bot -n 30 --no-pager

# API 日誌
sudo journalctl -u luckyred-api -n 30 --no-pager
```

### 3. 測試功能
1. **群組搜索**：
   - 在 MiniApp 中打開「發紅包」頁面
   - 點擊「選擇群組」
   - 測試搜索群組名稱、鏈接或用戶名

2. **發送紅包**：
   - 選擇群組
   - 選擇紅包類型（手氣最佳/紅包炸彈）
   - 發送紅包
   - 檢查是否成功發送到群組

3. **機器人不在群組**：
   - 選擇一個機器人不在的群組
   - 發送紅包
   - 檢查是否顯示分享鏈接

## 如果遇到問題

### Bot 無法啟動
```bash
# 查看錯誤日誌
sudo journalctl -u luckyred-bot -n 50 --no-pager | grep -i error

# 檢查 Bot Token
grep BOT_TOKEN /opt/luckyred/.env
```

### API 無法啟動
```bash
# 查看錯誤日誌
sudo journalctl -u luckyred-api -n 50 --no-pager | grep -i error

# 檢查依賴
cd /opt/luckyred/api
source .venv/bin/activate
pip install -r requirements.txt
```

### 前端構建失敗
```bash
# 清理並重新構建
cd /opt/luckyred/frontend
sudo rm -rf node_modules dist
npm install
npm run build
```

## 快速部署命令（一鍵執行）

```bash
cd /opt/luckyred && \
git pull origin master && \
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && \
sudo systemctl restart luckyred-api && \
sudo systemctl restart luckyred-bot && \
cd frontend && \
sudo rm -rf dist && \
npm run build && \
sudo systemctl reload nginx && \
echo "✅ 部署完成！"
```

