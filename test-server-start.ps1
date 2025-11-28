# 測試服務器啟動
$ErrorActionPreference = "Continue"
Set-Location "C:\hbgm001\frontend"

Write-Host "檢查環境..." -ForegroundColor Yellow
node --version
npm --version

Write-Host "`n檢查依賴..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "安裝依賴..." -ForegroundColor Yellow
    npm install
}

Write-Host "`n啟動服務器（前台運行，可以看到所有輸出）..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止`n" -ForegroundColor Gray

npm run dev

