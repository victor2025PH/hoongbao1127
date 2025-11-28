# 上傳 api.ts 到 GitHub
# 使用方法：在 PowerShell 中執行：.\上传api.ts到GitHub.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  上傳 api.ts 到 GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 進入項目目錄
Set-Location C:\hbgm001

# 檢查文件狀態
Write-Host "1. 檢查文件狀態..." -ForegroundColor Yellow
git status frontend/src/utils/api.ts

Write-Host ""
Write-Host "2. 添加 api.ts 文件..." -ForegroundColor Yellow
git add frontend/src/utils/api.ts

Write-Host ""
Write-Host "3. 提交更改..." -ForegroundColor Yellow
git commit -m "fix: 添加缺失的 API 函數 - searchChats, searchUsers, checkUserInChat 和 ChatInfo.link"

Write-Host ""
Write-Host "4. 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "   注意：如果提示需要認證，請使用 Personal Access Token" -ForegroundColor Gray
git push origin master

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！api.ts 已上傳到 GitHub" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：在服務器上執行：" -ForegroundColor Yellow
Write-Host "  cd /opt/luckyred" -ForegroundColor Gray
Write-Host "  git pull origin master" -ForegroundColor Gray
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm run build" -ForegroundColor Gray

