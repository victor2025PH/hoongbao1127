@echo off
REM ========================================
REM 完整測試：啟動後端和前端，測試搜索功能
REM ========================================
chcp 65001 >nul
setlocal enabledelayedexpansion

title 完整測試 - 後端和前端

echo.
echo ========================================
echo   完整測試：後端 + 前端 + 搜索測試
echo ========================================
echo.

REM 步驟 1: 檢查 .env 文件
echo [步驟 1/6] 檢查 .env 文件...
if not exist "%~dp0.env" (
    echo ❌ .env 文件不存在！
    echo.
    echo 請創建 .env 文件，內容包含:
    echo    BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
    echo    BOT_USERNAME=sucai2025_bot
    echo.
    pause
    exit /b 1
)
echo ✅ .env 文件存在
echo.

REM 步驟 2: 測試配置讀取
echo [步驟 2/6] 測試配置讀取...
cd /d "%~dp0api"
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); token_len = len(s.BOT_TOKEN); print('BOT_TOKEN 長度:', token_len); exit(0 if token_len > 0 else 1)" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ BOT_TOKEN 讀取失敗！
    echo.
    echo 請檢查:
    echo   1. .env 文件格式: BOT_TOKEN=你的token（無引號，無空格）
    echo   2. 文件編碼: UTF-8（無BOM）
    echo   3. python-dotenv 是否已安裝: pip install python-dotenv
    echo.
    pause
    exit /b 1
)
echo ✅ 配置讀取成功
echo.

REM 步驟 3: 檢查端口占用
echo [步驟 3/6] 檢查端口占用...
netstat -ano | findstr ":8080" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  端口 8080 已被占用
    echo    請先關閉占用端口的程序，或修改配置
    echo.
    pause
    exit /b 1
)
echo ✅ 端口 8080 可用
echo.

netstat -ano | findstr ":3001" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  端口 3001 已被占用
    echo    請先關閉占用端口的程序
    echo.
    pause
    exit /b 1
)
echo ✅ 端口 3001 可用
echo.

REM 步驟 4: 檢查依賴
echo [步驟 4/6] 檢查 Python 依賴...
python -c "import dotenv, pydantic_settings, uvicorn" 2>nul || (
    echo    正在安裝依賴...
    python -m pip install python-dotenv pydantic-settings uvicorn --quiet
)
echo ✅ Python 依賴就緒
echo.

REM 步驟 5: 檢查前端依賴
echo [步驟 5/6] 檢查前端依賴...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo    正在安裝前端依賴（這可能需要幾分鐘）...
    call npm install
) else (
    echo ✅ 前端依賴已安裝
)
echo.

REM 步驟 6: 啟動服務
echo [步驟 6/6] 準備啟動服務...
echo.
echo ========================================
echo   服務信息
echo ========================================
echo   後端 API: http://127.0.0.1:8080
echo   API 文檔: http://127.0.0.1:8080/docs
echo   前端: http://localhost:3001
echo ========================================
echo.
echo 將在 3 秒後啟動服務...
timeout /t 3 /nobreak >nul

REM 啟動後端（在新窗口）
echo 啟動後端服務器...
start "後端 API 服務器" cmd /k "cd /d %~dp0api && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080"

REM 等待後端啟動
echo 等待後端啟動（5秒）...
timeout /t 5 /nobreak >nul

REM 啟動前端（在新窗口）
echo 啟動前端服務器...
cd /d "%~dp0frontend"
start "前端開發服務器" cmd /k "npm run dev"

echo.
echo ========================================
echo   ✅ 服務已啟動
echo ========================================
echo.
echo 後端 API: http://127.0.0.1:8080/docs
echo 前端: http://localhost:3001
echo.
echo 請在瀏覽器中打開前端地址進行測試
echo 按任意鍵打開測試說明...
pause >nul

start "" "%~dp0測試說明.md"

