@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   全自動測試和啟動服務器
echo ========================================
echo.

cd /d C:\hbgm001

REM 步驟 1: 檢查 .env 文件
echo [步驟 1] 檢查 .env 文件...
if not exist ".env" (
    echo ❌ 錯誤: .env 文件不存在！
    echo    請在 C:\hbgm001\.env 創建 .env 文件
    echo    內容應包含: BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs
    pause
    exit /b 1
)
echo ✅ .env 文件存在
echo.

REM 步驟 2: 測試配置讀取
echo [步驟 2] 測試配置讀取...
cd api
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); print('BOT_TOKEN 長度:', len(s.BOT_TOKEN)); exit(0 if s.BOT_TOKEN else 1)" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 配置讀取失敗！
    echo.
    echo 可能的原因:
    echo   1. dotenv 未正確加載 .env 文件
    echo   2. pydantic-settings 未讀取環境變量
    echo   3. .env 文件格式不正確
    echo.
    pause
    exit /b 1
)
echo ✅ 配置讀取成功
echo.

REM 步驟 3: 檢查依賴
echo [步驟 3] 檢查依賴...
python -c "import uvicorn; print('✅ uvicorn 已安裝')" 2>nul || (echo ❌ uvicorn 未安裝 & pause & exit /b 1)
python -c "from dotenv import load_dotenv; print('✅ python-dotenv 已安裝')" 2>nul || (echo ❌ python-dotenv 未安裝 & pause & exit /b 1)
python -c "from pydantic_settings import BaseSettings; print('✅ pydantic-settings 已安裝')" 2>nul || (echo ❌ pydantic-settings 未安裝 & pause & exit /b 1)
echo.

REM 步驟 4: 啟動服務器
echo [步驟 4] 啟動服務器...
echo   服務器地址: http://127.0.0.1:8000
echo   API 文檔: http://127.0.0.1:8000/docs
echo   按 Ctrl+C 停止服務器
echo.
echo ========================================
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

