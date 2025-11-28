# 設置輸出編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  配置測試和服務器啟動" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 測試配置讀取
Write-Host "[步驟 1] 測試配置讀取..." -ForegroundColor Yellow
Write-Host ""

Set-Location C:\hbgm001\api

$testScript = @"
import sys
sys.path.insert(0, '..')
from shared.config.settings import get_settings, ENV_FILE
print('ENV_FILE:', ENV_FILE)
print('文件存在:', ENV_FILE.exists())
s = get_settings()
print('BOT_TOKEN 長度:', len(s.BOT_TOKEN))
if s.BOT_TOKEN:
    print('✅ BOT_TOKEN 讀取成功！')
    print('BOT_TOKEN 前20字符:', s.BOT_TOKEN[:20])
else:
    print('❌ BOT_TOKEN 為空！')
"@

# 使用 ProcessStartInfo 來捕獲輸出
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "python"
$psi.Arguments = "-c `"$testScript`""
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$psi.WorkingDirectory = "C:\hbgm001\api"

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi

try {
    $process.Start() | Out-Null
    $output = $process.StandardOutput.ReadToEnd()
    $error = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    
    Write-Host $output
    if ($error) {
        Write-Host $error -ForegroundColor Red
    }
    
    Write-Host ""
    
    if ($process.ExitCode -eq 0) {
        Write-Host "[步驟 2] 配置讀取成功，準備啟動服務器..." -ForegroundColor Green
        Write-Host ""
        Write-Host "服務器將在 http://127.0.0.1:8000 啟動" -ForegroundColor Cyan
        Write-Host "按 Ctrl+C 停止服務器" -ForegroundColor Gray
        Write-Host ""
        
        # 啟動服務器（前台運行）
        python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
    } else {
        Write-Host "[錯誤] 配置讀取失敗，退出代碼: $($process.ExitCode)" -ForegroundColor Red
        Write-Host ""
        Write-Host "請檢查:" -ForegroundColor Yellow
        Write-Host "  1. .env 文件是否存在於 C:\hbgm001\.env" -ForegroundColor Yellow
        Write-Host "  2. .env 文件格式是否正確（BOT_TOKEN=...）" -ForegroundColor Yellow
        Write-Host "  3. python-dotenv 是否已安裝" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "執行錯誤: $_" -ForegroundColor Red
    exit 1
}

