@echo off
chcp 65001 >nul
echo ========================================
echo 配置測試和服務器啟動
echo ========================================
echo.

cd /d C:\hbgm001\api

echo [步驟 1] 測試配置讀取...
echo.
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空')"
echo.

if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] 配置讀取失敗
    echo.
    echo 請檢查:
    echo   1. .env 文件是否存在於 C:\hbgm001\.env
    echo   2. .env 文件格式是否正確（BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs）
    echo   3. python-dotenv 是否已安裝: pip install python-dotenv
    pause
    exit /b 1
)

echo [步驟 2] 啟動服務器...
echo.
echo 服務器將在 http://127.0.0.1:8000 啟動
echo 按 Ctrl+C 停止服務器
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

