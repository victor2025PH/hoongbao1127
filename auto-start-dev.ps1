# 自動啟動並監控開發服務器
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  自動啟動前端開發服務器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 進入前端目錄
$frontendPath = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendPath

Write-Host "`n[1/4] 檢查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js 版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/4] 檢查依賴..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "正在安裝依賴..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 依賴安裝失敗" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 依賴安裝完成" -ForegroundColor Green
} else {
    Write-Host "✓ 依賴已存在" -ForegroundColor Green
}

Write-Host "`n[3/4] 檢查端口 3001..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠ 端口 3001 已被占用，嘗試終止進程..." -ForegroundColor Yellow
    $process = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "✓ 已釋放端口" -ForegroundColor Green
    }
}

Write-Host "`n[4/4] 啟動開發服務器..." -ForegroundColor Yellow
Write-Host "服務器將在 http://localhost:3001 運行" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服務器`n" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 啟動開發服務器
try {
    npm run dev
} catch {
    Write-Host "`n✗ 啟動失敗: $_" -ForegroundColor Red
    Write-Host "`n嘗試修復..." -ForegroundColor Yellow
    
    # 清理並重新安裝
    Remove-Item -Path "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "package-lock.json" -Force -ErrorAction SilentlyContinue
    npm install
    npm run dev
}

