@echo off
chcp 65001 >nul
echo ========================================
echo 啟動 API 服務器
echo ========================================
echo.

cd /d C:\hbgm001\api
echo 正在啟動服務器...
echo 服務器地址: http://127.0.0.1:8000
echo 按 Ctrl+C 停止服務器
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

