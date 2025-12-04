# 執行部署腳本
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  更新服務器 Bot 菜單" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# 步驟 1: 檢查本地更改
Write-Host "[1/6] 檢查本地更改..." -ForegroundColor Yellow
Set-Location "c:\hbgm001"
$status = git status --short
if ($status) {
    Write-Host "發現未提交的更改:" -ForegroundColor Yellow
    Write-Host $status
} else {
    Write-Host "✓ 沒有未提交的更改" -ForegroundColor Green
}
Write-Host ""

# 步驟 2: 提交更改
Write-Host "[2/6] 提交更改..." -ForegroundColor Yellow
git add -A
$commitResult = git commit -m "fix: 更新 Bot 菜單和餘額查詢邏輯" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 已提交更改" -ForegroundColor Green
} else {
    Write-Host "沒有需要提交的更改或提交失敗" -ForegroundColor Gray
}
Write-Host ""

# 步驟 3: 推送到遠程
Write-Host "[3/6] 推送到遠程倉庫..." -ForegroundColor Yellow
$pushResult = git push origin master 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 推送成功" -ForegroundColor Green
} else {
    Write-Host "✗ 推送失敗: $pushResult" -ForegroundColor Red
    Write-Host "繼續執行服務器更新..." -ForegroundColor Yellow
}
Write-Host ""

# 步驟 4: 更新服務器代碼
Write-Host "[4/6] 更新服務器代碼..." -ForegroundColor Yellow
$serverCmd = "cd /opt/luckyred && echo '=== 更新前提交 ===' && git log --oneline -1 && echo '' && echo '=== 拉取最新代碼 ===' && git fetch origin && git reset --hard origin/master && echo '✓ 代碼已更新' && echo '' && echo '=== 更新後提交 ===' && git log --oneline -1"
$updateResult = ssh ubuntu@165.154.254.99 $serverCmd 2>&1
Write-Host $updateResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 服務器代碼已更新" -ForegroundColor Green
} else {
    Write-Host "✗ 服務器更新失敗" -ForegroundColor Red
}
Write-Host ""

# 步驟 5: 驗證文件
Write-Host "[5/6] 驗證關鍵文件..." -ForegroundColor Yellow
$verifyCmd = "cd /opt/luckyred && echo '檢查文件:' && ls -lh bot/keyboards/reply_keyboards.py bot/handlers/start.py 2>&1 && echo '' && echo '檢查 start.py:' && grep -n 'get_main_reply_keyboard' bot/handlers/start.py 2>&1 | head -3"
$verifyResult = ssh ubuntu@165.154.254.99 $verifyCmd 2>&1
Write-Host $verifyResult
Write-Host ""

# 步驟 6: 重啟服務
Write-Host "[6/6] 重啟 Bot 服務..." -ForegroundColor Yellow
$restartCmd = "sudo systemctl restart luckyred-bot && sleep 3 && echo '✓ 服務已重啟' && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-bot && echo '' && echo '=== 服務日誌（最後 15 行）===' && sudo journalctl -u luckyred-bot -n 15 --no-pager"
$restartResult = ssh ubuntu@165.154.254.99 $restartCmd 2>&1
Write-Host $restartResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 服務重啟成功" -ForegroundColor Green
} else {
    Write-Host "✗ 服務重啟失敗" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "請在 Telegram 中測試：" -ForegroundColor Yellow
Write-Host "  1. 發送 /start 給 @sucai2025_bot" -ForegroundColor White
Write-Host "  2. 應該看到多級菜單按鈕（在輸入框下方）" -ForegroundColor White
Write-Host "  3. 檢查錢包餘額是否正確顯示" -ForegroundColor White
Write-Host ""
