@echo off
REM ========================================
REM 一鍵測試配置並啟動服務器
REM ========================================
chcp 65001 >nul
setlocal enabledelayedexpansion

title 配置測試和服務器啟動

echo.
echo ========================================
echo   一鍵測試和啟動服務器
echo ========================================
echo.

REM 檢查 .env 文件
echo [步驟 1/4] 檢查 .env 文件...
if not exist "%~dp0.env" (
    echo.
    echo ❌ 錯誤: .env 文件不存在！
    echo.
    echo 請在以下位置創建 .env 文件:
    echo    %~dp0.env
    echo.
    echo 文件內容應包含:
    echo    BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
    echo    BOT_USERNAME=sucai2025_bot
    echo.
    pause
    exit /b 1
)
echo ✅ .env 文件存在
echo.

REM 檢查 Python 依賴
echo [步驟 2/4] 檢查 Python 依賴...
cd /d "%~dp0api"

python -c "import dotenv; print('✅ python-dotenv')" 2>nul || (
    echo   正在安裝 python-dotenv...
    python -m pip install python-dotenv --quiet
)

python -c "import pydantic_settings; print('✅ pydantic-settings')" 2>nul || (
    echo   正在安裝 pydantic-settings...
    python -m pip install pydantic-settings --quiet
)

python -c "import uvicorn; print('✅ uvicorn')" 2>nul || (
    echo   正在安裝 uvicorn...
    python -m pip install uvicorn --quiet
)

echo ✅ 所有依賴已就緒
echo.

REM 測試配置讀取
echo [步驟 3/4] 測試配置讀取...
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('   BOT_TOKEN 長度:', len(s.BOT_TOKEN)); print('   BOT_TOKEN:', s.BOT_TOKEN[:30] if s.BOT_TOKEN else '空'); exit(0 if s.BOT_TOKEN else 1)" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 配置讀取失敗！
    echo.
    echo 可能的原因:
    echo   1. .env 文件格式不正確
    echo   2. BOT_TOKEN 值為空
    echo   3. 文件編碼問題
    echo.
    echo 請檢查 .env 文件，確保包含:
    echo   BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
    echo   注意: 不要有引號，不要有多餘空格
    echo.
    pause
    exit /b 1
)

echo ✅ 配置讀取成功
echo.

REM 啟動服務器
echo [步驟 4/4] 啟動服務器...
echo.
echo ========================================
echo   服務器信息
echo ========================================
echo   地址: http://127.0.0.1:8000
echo   API 文檔: http://127.0.0.1:8000/docs
echo   按 Ctrl+C 停止服務器
echo ========================================
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 服務器啟動失敗
    echo.
    pause
    exit /b 1
)

pause


