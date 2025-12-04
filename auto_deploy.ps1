# Lucky Red 自動部署腳本
# 執行方式: 右鍵點擊此文件 -> "使用 PowerShell 執行"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Lucky Red 自動部署腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切換到項目目錄
Set-Location c:\hbgm001

# 1. 檢查 Git 狀態
Write-Host "[1/4] 檢查 Git 狀態..." -ForegroundColor Yellow
git status --short
Write-Host ""

# 2. 提交更改
Write-Host "[2/4] 提交所有更改..." -ForegroundColor Yellow
git add -A
git commit -m "feat: 完成四大功能模塊 - HTTPS/邀請系統/群組通知/管理後台"
Write-Host ""

# 3. 推送到 GitHub
Write-Host "[3/4] 推送到 GitHub..." -ForegroundColor Yellow
git push origin master
Write-Host ""

# 4. 部署到服務器
Write-Host "[4/4] 部署到服務器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "請在服務器 SSH 終端執行以下命令：" -ForegroundColor Green
Write-Host ""
Write-Host "cd /opt/luckyred && git pull origin master" -ForegroundColor White
Write-Host "mkdir -p /opt/luckyred/api/services" -ForegroundColor White
Write-Host "sudo systemctl restart luckyred-api luckyred-bot" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   本地部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# 等待用戶按鍵
Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
