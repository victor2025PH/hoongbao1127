@echo off
chcp 65001
title 啟動本地測試服務器

echo ========================================
echo   啟動本地測試服務器
echo ========================================
echo.

cd /d C:\hbgm001

echo [步驟 1] 檢查文件...
if exist "api\routers\chats.py" (
    echo ✅ chats.py 存在
) else (
    echo ❌ chats.py 不存在
    pause
    exit /b 1
)

if exist "api\main.py" (
    echo ✅ main.py 存在
) else (
    echo ❌ main.py 不存在
    pause
    exit /b 1
)

echo.
echo [步驟 2] 檢查路由註冊...
findstr /C:"from api.routers import.*chats" api\main.py >nul
if %errorlevel% equ 0 (
    echo ✅ chats 路由已導入
) else (
    echo ❌ chats 路由未導入
)

findstr /C:"chats.router" api\main.py >nul
if %errorlevel% equ 0 (
    echo ✅ chats 路由已註冊
) else (
    echo ❌ chats 路由未註冊
)

echo.
echo [步驟 3] 啟動 API 服務器...
echo 請在新的終端窗口中執行:
echo   cd C:\hbgm001\api
echo   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo 或者如果使用虛擬環境:
echo   cd C:\hbgm001\api
echo   .venv\Scripts\activate
echo   uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo [步驟 4] 啟動前端服務器...
echo 請在另一個終端窗口中執行:
echo   cd C:\hbgm001\frontend
echo   npm run dev
echo.
echo ========================================
echo   準備完成
echo ========================================
echo.
echo 測試 API 端點:
echo   http://localhost:8000/api/v1/chats/search?q=minihb2
echo.
pause

