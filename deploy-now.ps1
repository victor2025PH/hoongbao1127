# 快速部署腳本 - 直接執行
$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LuckyRed 全自動部署" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 檢查 Git 狀態
Write-Host "[1/4] 檢查 Git 狀態..." -ForegroundColor Yellow
Set-Location "C:\hbgm001"
$status = git status --short
if ($status) {
    Write-Host "未提交的更改：" -ForegroundColor Red
    Write-Host $status
}

# 2. 推送代碼（如果有未推送的）
Write-Host "`n[2/4] 檢查未推送的提交..." -ForegroundColor Yellow
$unpushed = git log origin/master..HEAD --oneline 2>$null
if ($unpushed) {
    Write-Host "發現未推送的提交，正在推送..." -ForegroundColor Yellow
    git push origin master
}

# 3. 執行部署
Write-Host "`n[3/4] 連接到服務器並部署..." -ForegroundColor Yellow
Write-Host "服務器: ubuntu@165.154.254.99" -ForegroundColor Cyan
Write-Host ""

$deployCmd = @"
cd /opt/luckyred && \
echo '=== 拉取最新代碼 ===' && \
git pull origin master && \
echo '' && \
echo '=== 構建前端 ===' && \
cd frontend && \
npm install --silent && \
npm run build && \
echo '' && \
echo '=== 重啟服務 ===' && \
sudo systemctl restart luckyred-api luckyred-bot luckyred-admin && \
echo '' && \
echo '=== 服務狀態 ===' && \
sudo systemctl status luckyred-api --no-pager | head -8 && \
echo '' && \
sudo systemctl status luckyred-bot --no-pager | head -8
"@

Write-Host "正在執行部署命令..." -ForegroundColor Green
Write-Host "（如果需要密碼，請輸入 SSH 密碼）`n" -ForegroundColor Yellow

ssh ubuntu@165.154.254.99 $deployCmd

# 4. 完成
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green
Write-Host "MiniApp: https://mini.usdt2026.cc" -ForegroundColor Cyan
Write-Host "Admin: https://admin.usdt2026.cc`n" -ForegroundColor Cyan
