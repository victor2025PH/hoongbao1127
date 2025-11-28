# 直接部署腳本 - 使用 PowerShell SSH
$ErrorActionPreference = "Continue"

$Server = "165.154.254.99"
$User = "ubuntu"
$RemotePath = "/opt/luckyred"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  直接部署到服務器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 測試 SSH 連接
Write-Host "[測試] SSH 連接..." -ForegroundColor Yellow
try {
    $testResult = ssh -o ConnectTimeout=5 -o BatchMode=yes "${User}@${Server}" "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  SSH 需要密碼或未配置密鑰" -ForegroundColor Yellow
        Write-Host "請在提示時輸入 SSH 密碼" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "✅ SSH 連接正常" -ForegroundColor Green
        Write-Host ""
    }
} catch {
    Write-Host "❌ SSH 連接失敗: $_" -ForegroundColor Red
    exit 1
}

# 步驟 1: 檢查當前狀態
Write-Host "[1/7] 檢查當前狀態..." -ForegroundColor Yellow
ssh "${User}@${Server}" "cd ${RemotePath} && echo '當前目錄:' && pwd && echo 'Git 狀態:' && git status --short && echo '最新提交:' && git log --oneline -1"
Write-Host ""

# 步驟 2: 拉取代碼
Write-Host "[2/7] 拉取最新代碼..." -ForegroundColor Yellow
$pullResult = ssh "${User}@${Server}" "cd ${RemotePath} && git pull origin master 2>&1"
Write-Host $pullResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git pull 失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 代碼更新完成" -ForegroundColor Green
Write-Host ""

# 步驟 3: 更新 Bot Token
Write-Host "[3/7] 更新 Bot Token..." -ForegroundColor Yellow
ssh "${User}@${Server}" "cd ${RemotePath} && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && echo 'Bot Token:' && grep BOT_TOKEN .env | cut -d'=' -f2 | cut -c1-30"
Write-Host "✅ Bot Token 已更新" -ForegroundColor Green
Write-Host ""

# 步驟 4: 重啟 API
Write-Host "[4/7] 重啟 API 服務..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api && echo 'API: Active'"
Write-Host "✅ API 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 5: 重啟 Bot
Write-Host "[5/7] 重啟 Bot 服務..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot && echo 'Bot: Active'"
Write-Host "✅ Bot 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 6: 構建前端
Write-Host "[6/7] 構建前端（這可能需要幾分鐘）..." -ForegroundColor Yellow
ssh "${User}@${Server}" "cd ${RemotePath}/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -10"
Write-Host "✅ 前端構建完成" -ForegroundColor Green
Write-Host ""

# 步驟 7: 重載 Nginx
Write-Host "[7/7] 重載 Nginx..." -ForegroundColor Yellow
ssh "${User}@${Server}" "sudo systemctl reload nginx && echo 'Nginx reloaded'"
Write-Host "✅ Nginx 已重載" -ForegroundColor Green
Write-Host ""

# 最終檢查
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  部署完成！服務狀態：" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
ssh "${User}@${Server}" "echo 'Bot:' && sudo systemctl is-active luckyred-bot && echo 'API:' && sudo systemctl is-active luckyred-api && echo 'Nginx:' && sudo systemctl is-active nginx"
Write-Host ""

