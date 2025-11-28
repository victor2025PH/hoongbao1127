# 完整自動化部署腳本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完整自動化部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\hbgm001

# 1. 添加所有文件
Write-Host "[1/4] 添加所有修改的文件..." -ForegroundColor Yellow
git add -A
$status = git status --short
if ($status) {
    Write-Host $status
} else {
    Write-Host "沒有需要提交的文件"
}
Write-Host ""

# 2. 提交
Write-Host "[2/4] 提交更改..." -ForegroundColor Yellow
git commit -m "fix: 完整更新 - 改進群組搜索邏輯、確保 t.me 鏈接始終返回結果"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 提交成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  沒有新更改或提交失敗" -ForegroundColor Yellow
}
Write-Host ""

# 3. 推送
Write-Host "[3/4] 推送到 GitHub..." -ForegroundColor Yellow
git push origin master
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 已推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失敗！" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. 顯示最新提交
Write-Host "[4/4] 最新提交:" -ForegroundColor Yellow
git log --oneline -1
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 本地操作完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：在服務器上執行：" -ForegroundColor Yellow
Write-Host "  ssh ubuntu@165.154.254.99" -ForegroundColor Gray
Write-Host "  cd /opt/luckyred" -ForegroundColor Gray
Write-Host "  git pull origin master" -ForegroundColor Gray
Write-Host "  sudo systemctl restart luckyred-api" -ForegroundColor Gray
Write-Host ""

