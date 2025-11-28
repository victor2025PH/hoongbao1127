# 全自動部署腳本 - 直接執行，無需手動操作
$ErrorActionPreference = "Continue"

$Server = "165.154.254.99"
$User = "ubuntu"
$RemotePath = "/opt/luckyred"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  全自動部署 Lucky Red MiniApp" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 拉取代碼
Write-Host "[1/6] 拉取最新代碼..." -ForegroundColor Yellow
$result = ssh "${User}@${Server}" "cd ${RemotePath} && git pull origin master 2>&1"
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git pull 失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 代碼更新完成" -ForegroundColor Green
Write-Host ""

# 步驟 2: 更新 Bot Token
Write-Host "[2/6] 更新 Bot Token..." -ForegroundColor Yellow
ssh "${User}@${Server}" "cd ${RemotePath} && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && echo 'Bot Token updated'"
Write-Host "✅ Bot Token 已更新" -ForegroundColor Green
Write-Host ""

# 步驟 3: 重啟 API
Write-Host "[3/6] 重啟 API 服務..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api"
Write-Host "✅ API 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 4: 重啟 Bot
Write-Host "[4/6] 重啟 Bot 服務..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot"
Write-Host "✅ Bot 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 5: 構建前端
Write-Host "[5/6] 構建前端（這可能需要幾分鐘）..." -ForegroundColor Yellow
ssh "${User}@${Server}" "cd ${RemotePath}/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -10"
Write-Host "✅ 前端構建完成" -ForegroundColor Green
Write-Host ""

# 步驟 6: 重載 Nginx
Write-Host "[6/6] 重載 Nginx..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl reload nginx && echo 'Nginx reloaded'"
Write-Host "✅ Nginx 已重載" -ForegroundColor Green
Write-Host ""

# 最終檢查
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  部署完成！服務狀態：" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
ssh "${User}@${Server}" "echo 'Bot:' && sudo systemctl is-active luckyred-bot && echo 'API:' && sudo systemctl is-active luckyred-api && echo 'Nginx:' && sudo systemctl is-active nginx"
Write-Host ""

