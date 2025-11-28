@echo off
chcp 65001
title 啟動 API 服務器

echo ========================================
echo   啟動 API 服務器
echo ========================================
echo.

cd /d C:\hbgm001\api

echo [步驟 1] 檢查 Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python 未找到
    pause
    exit /b 1
)

echo.
echo [步驟 2] 檢查依賴...
python -m pip show uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  uvicorn 未安裝，正在安裝...
    python -m pip install uvicorn fastapi
)

echo.
echo [步驟 3] 檢查代碼語法...
python -m py_compile main.py
if %errorlevel% neq 0 (
    echo ❌ main.py 語法錯誤
    pause
    exit /b 1
)

python -m py_compile routers/chats.py
if %errorlevel% neq 0 (
    echo ❌ routers/chats.py 語法錯誤
    pause
    exit /b 1
)

echo ✅ 語法檢查通過
echo.
echo [步驟 4] 啟動服務器...
echo.
echo 服務器將在 http://127.0.0.1:8000 啟動
echo 按 Ctrl+C 停止服務器
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

