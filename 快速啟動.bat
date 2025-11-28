@echo off
REM ========================================
REM 快速啟動後端和前端
REM ========================================
chcp 65001 >nul

title 快速啟動服務

echo.
echo ========================================
echo   快速啟動服務
echo ========================================
echo.

REM 檢查配置
cd /d "%~dp0api"
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); exit(0 if len(s.BOT_TOKEN) > 0 else 1)" 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo ❌ BOT_TOKEN 未配置！
    echo.
    echo 請先運行: 診斷BOT_TOKEN.bat
    echo 或檢查 .env 文件
    echo.
    pause
    exit /b 1
)

echo ✅ 配置檢查通過
echo.

REM 啟動後端
echo 啟動後端服務器（端口 8080）...
start "後端 API" cmd /k "cd /d %~dp0api && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080"

REM 等待後端啟動
timeout /t 3 /nobreak >nul

REM 啟動前端
echo 啟動前端服務器（端口 3001）...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo 正在安裝前端依賴...
    call npm install
)

start "前端開發" cmd /k "npm run dev"

echo.
echo ========================================
echo   ✅ 服務已啟動
echo ========================================
echo.
echo 後端: http://127.0.0.1:8080/docs
echo 前端: http://localhost:3001
echo.
echo 請在瀏覽器中打開前端地址進行測試
echo.
pause

