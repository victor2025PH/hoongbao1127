# 快速上傳修復文件到 GitHub
# 使用方法：在 PowerShell 中執行：.\快速上传到GitHub.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  上傳修復文件到 GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 進入項目目錄
Set-Location C:\hbgm001

# 檢查 Git 狀態
Write-Host "1. 檢查 Git 狀態..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "2. 添加修復的文件..." -ForegroundColor Yellow
git add frontend/src/pages/SendRedPacket.tsx
git add frontend/src/providers/I18nProvider.tsx

Write-Host ""
Write-Host "3. 提交更改..." -ForegroundColor Yellow
git commit -m "fix: 修復 TypeScript 編譯錯誤 - bomb_number 類型和 view_rules 重複問題"

Write-Host ""
Write-Host "4. 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "   注意：如果提示需要認證，請使用 Personal Access Token" -ForegroundColor Gray
git push origin master

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  完成！請檢查 GitHub 倉庫確認上傳成功" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

