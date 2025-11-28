@echo off
REM ========================================
REM 開始測試：啟動後端和前端
REM ========================================
chcp 65001 >nul

title 開始測試 - 後端和前端

echo.
echo ========================================
echo   開始測試：後端 + 前端
echo ========================================
echo.

REM 檢查配置
echo [1/4] 檢查配置...
cd /d "%~dp0api"
python -c "import sys; sys.path.insert(0, '..'); from shared.config.settings import get_settings; s = get_settings(); exit(0 if len(s.BOT_TOKEN) > 0 else 1)" 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo ❌ BOT_TOKEN 未配置！
    echo.
    echo 請先運行: 修復ENV文件.py
    echo.
    pause
    exit /b 1
)
echo ✅ 配置檢查通過
echo.

REM 檢查端口
echo [2/4] 檢查端口...
netstat -ano | findstr ":8080" >nul
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  端口 8080 已被占用
    echo    請先關閉占用端口的程序
    echo.
    pause
    exit /b 1
)
echo ✅ 端口 8080 可用

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

REM 檢查依賴
echo [3/4] 檢查依賴...
python -c "import dotenv, pydantic_settings, uvicorn" 2>nul || (
    echo    正在安裝 Python 依賴...
    python -m pip install python-dotenv pydantic-settings uvicorn --quiet
)
echo ✅ Python 依賴就緒

cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo    正在安裝前端依賴（這可能需要幾分鐘）...
    call npm install
) else (
    echo ✅ 前端依賴已安裝
)
echo.

REM 啟動服務
echo [4/4] 啟動服務...
echo.
echo ========================================
echo   服務信息
echo ========================================
echo   後端 API: http://127.0.0.1:8080
echo   API 文檔: http://127.0.0.1:8080/docs
echo   前端: http://localhost:3001
echo ========================================
echo.

REM 啟動後端
echo 啟動後端服務器...
start "後端 API 服務器" cmd /k "cd /d %~dp0api && echo 後端服務器啟動中... && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080"

REM 等待後端啟動
echo 等待後端啟動（5秒）...
timeout /t 5 /nobreak >nul

REM 啟動前端
echo 啟動前端服務器...
cd /d "%~dp0frontend"
start "前端開發服務器" cmd /k "echo 前端服務器啟動中... && npm run dev"

echo.
echo ========================================
echo   ✅ 服務已啟動
echo ========================================
echo.
echo 後端 API 文檔: http://127.0.0.1:8080/docs
echo 前端應用: http://localhost:3001
echo.
echo 測試步驟:
echo   1. 打開 http://127.0.0.1:8080/docs 查看 API 文檔
echo   2. 打開 http://localhost:3001 使用前端應用
echo   3. 在前端搜索群組或用戶進行測試
echo.
echo 按任意鍵打開測試說明...
pause >nul

if exist "%~dp0測試說明.md" (
    start "" "%~dp0測試說明.md"
)

