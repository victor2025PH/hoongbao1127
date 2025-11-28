# 強制設置輸出編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# 禁用輸出緩衝
$PSDefaultParameterValues['*:NoNewline'] = $false

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PowerShell 輸出測試" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[測試 1] 基本輸出" -ForegroundColor Yellow
Write-Host "  這是一條測試消息" -ForegroundColor Green
Write-Host ""

Write-Host "[測試 2] 命令執行" -ForegroundColor Yellow
Get-Location | Write-Host -ForegroundColor Cyan
Write-Host ""

Write-Host "[測試 3] Python 命令" -ForegroundColor Yellow
python --version 2>&1 | Write-Host
Write-Host ""

Write-Host "[測試 4] 配置讀取測試" -ForegroundColor Yellow
Set-Location C:\hbgm001\api
$pythonCmd = @"
import sys
sys.path.insert(0, '..')
from shared.config.settings import get_settings
s = get_settings()
print('BOT_TOKEN 長度:', len(s.BOT_TOKEN))
print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')
"@

$output = python -c $pythonCmd 2>&1
Write-Host $output
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "測試完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan


