# 確保開發服務器運行
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  確保開發服務器運行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$frontendPath = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendPath

# 檢查並安裝依賴
if (-not (Test-Path "node_modules")) {
    Write-Host "`n[安裝] 正在安裝依賴..." -ForegroundColor Yellow
    npm install
}

# 檢查端口是否被占用
$portCheck = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "`n[發現] 端口 3001 已被占用" -ForegroundColor Yellow
    $processId = $portCheck.OwningProcess
    Write-Host "[終止] 正在終止進程 $processId..." -ForegroundColor Yellow
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 啟動服務器
Write-Host "`n[啟動] 正在啟動開發服務器..." -ForegroundColor Yellow
$process = Start-Process -FilePath "npm" -ArgumentList "run","dev" -PassThru -NoNewWindow

# 等待服務器啟動
Write-Host "[等待] 等待服務器啟動..." -ForegroundColor Yellow
$maxWait = 30
$waited = 0
$serverReady = $false

while ($waited -lt $maxWait -and -not $serverReady) {
    Start-Sleep -Seconds 1
    $waited++
    
    $portCheck = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
    if ($portCheck) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            $serverReady = $true
            Write-Host "`n[成功] 服務器已啟動！" -ForegroundColor Green
            Write-Host "[地址] http://localhost:3001" -ForegroundColor Cyan
            Write-Host "`n服務器正在運行，按 Ctrl+C 停止" -ForegroundColor Gray
        } catch {
            # 繼續等待
        }
    }
    
    if ($waited % 5 -eq 0) {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $serverReady) {
    Write-Host "`n[錯誤] 服務器啟動超時" -ForegroundColor Red
    Write-Host "[檢查] 請查看錯誤信息" -ForegroundColor Yellow
    exit 1
}

# 保持運行
try {
    Wait-Process -Id $process.Id
} catch {
    Write-Host "`n服務器已停止" -ForegroundColor Yellow
}

