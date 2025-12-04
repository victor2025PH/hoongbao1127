# ============================================
# Lucky Red 服務啟動腳本
# ============================================

Write-Host ""
Write-Host "🚀 啟動 Lucky Red 服務..." -ForegroundColor Green
Write-Host ""

$projectRoot = $PSScriptRoot
if (-not $projectRoot) {
    $projectRoot = Get-Location
}

# 檢查虛擬環境
if (-not (Test-Path "$projectRoot\api\.venv")) {
    Write-Host "✗ API 虛擬環境不存在" -ForegroundColor Red
    Write-Host "請先運行: .\setup-and-deploy.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "$projectRoot\bot\.venv")) {
    Write-Host "✗ Bot 虛擬環境不存在" -ForegroundColor Red
    Write-Host "請先運行: .\setup-and-deploy.ps1" -ForegroundColor Yellow
    exit 1
}

# 啟動 API
Write-Host "啟動 API 服務器..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot\api'; .venv\Scripts\Activate.ps1; Write-Host '🚀 API 服務器 (http://localhost:8080)' -ForegroundColor Green; Write-Host '📚 API 文檔: http://localhost:8080/docs' -ForegroundColor Cyan; Write-Host ''; uvicorn main:app --host 0.0.0.0 --port 8080 --reload"
)

# 等待一下
Start-Sleep -Seconds 3

# 停止舊的 Bot 實例（如果存在）
Write-Host "檢查並停止舊的 Bot 實例..." -ForegroundColor Cyan
$botProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CommandLine)
    $cmdLine -like "*bot*main.py*" -or $cmdLine -like "*hbgm001\bot*"
}
if ($botProcesses) {
    Write-Host "發現 $($botProcesses.Count) 個舊的 Bot 實例，正在停止..." -ForegroundColor Yellow
    $botProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "舊實例已停止" -ForegroundColor Green
}

# 啟動 Bot
Write-Host "啟動 Bot..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot\bot'; .venv\Scripts\Activate.ps1; Write-Host '🤖 Telegram Bot 啟動中...' -ForegroundColor Green; Write-Host ''; python main.py"
)

Write-Host ""
Write-Host "✅ 服務已啟動！" -ForegroundColor Green
Write-Host ""
Write-Host "服務信息：" -ForegroundColor Yellow
Write-Host "  • API: http://localhost:8080" -ForegroundColor Cyan
Write-Host "  • API 文檔: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "  • Bot: 運行中（查看 Bot 窗口）" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: Close the service windows to stop services" -ForegroundColor Gray
Write-Host ""
