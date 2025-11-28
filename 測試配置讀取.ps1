# 設置輸出編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "測試配置讀取" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 設置工作目錄
Set-Location C:\hbgm001\api

# 執行 Python 測試
$pythonOutput = python -c @"
import sys
sys.path.insert(0, '..')
from shared.config.settings import get_settings, ENV_FILE
print('ENV_FILE:', ENV_FILE)
print('文件存在:', ENV_FILE.exists())
s = get_settings()
print('BOT_TOKEN 長度:', len(s.BOT_TOKEN))
if s.BOT_TOKEN:
    print('BOT_TOKEN 前20字符:', s.BOT_TOKEN[:20])
    print('BOT_TOKEN 後10字符:', s.BOT_TOKEN[-10:])
else:
    print('BOT_TOKEN: 空')
"@ 2>&1

# 顯示輸出
Write-Host $pythonOutput

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "按任意鍵繼續..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

