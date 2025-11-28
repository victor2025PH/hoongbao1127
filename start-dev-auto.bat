@echo off
chcp 65001 >nul
title 前端開發服務器 - 自動監控

:start
cls
echo ==========================================
echo   前端開發服務器 - 自動啟動和監控
echo ==========================================
echo.

cd /d "%~dp0frontend"

echo [1] 檢查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Node.js 未安裝或不在 PATH 中
    pause
    exit /b 1
)
node --version
echo.

echo [2] 檢查依賴...
if not exist "node_modules" (
    echo [安裝] 正在安裝依賴...
    call npm install
    if errorlevel 1 (
        echo [錯誤] 依賴安裝失敗
        pause
        exit /b 1
    )
) else (
    echo [OK] 依賴已存在
)
echo.

echo [3] 檢查端口 3001...
netstat -ano | findstr ":3001" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 3001 已被占用
    echo [嘗試] 正在終止占用進程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo.

echo [4] 啟動開發服務器...
echo ==========================================
echo 服務器地址: http://localhost:3001
echo 按 Ctrl+C 停止服務器
echo ==========================================
echo.

call npm run dev

if errorlevel 1 (
    echo.
    echo [錯誤] 服務器啟動失敗
    echo [修復] 正在清理並重新安裝依賴...
    echo.
    rmdir /s /q node_modules 2>nul
    del package-lock.json 2>nul
    call npm install
    echo.
    echo [重試] 重新啟動服務器...
    call npm run dev
)

pause

