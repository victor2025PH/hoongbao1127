@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   LuckyRed 本地開發環境啟動
echo ========================================
echo.

cd /d C:\hbgm001

echo [1/5] 檢查環境配置...
if not exist .env (
    echo ⚠️  .env 文件不存在，從 .env.example 創建...
    if exist .env.example (
        copy .env.example .env
        echo ✓ 已創建 .env 文件，請編輯填入實際值
        echo   重要：請編輯 .env 文件填入 BOT_TOKEN 和 DATABASE_URL
    ) else (
        echo ✗ .env.example 文件不存在
        pause
        exit /b 1
    )
) else (
    echo ✓ .env 文件存在
)

echo.
echo [2/5] 檢查 Python 環境...
if not exist api\.venv (
    echo 創建 API 虛擬環境...
    python -m venv api\.venv
    echo ✓ 虛擬環境已創建
)

echo 安裝 API 依賴...
call api\.venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
echo ✓ API 依賴已安裝

echo.
echo [3/5] 檢查前端依賴...
if not exist frontend\node_modules (
    echo 安裝前端依賴...
    cd frontend
    call npm install
    cd ..
    echo ✓ 前端依賴已安裝
) else (
    echo ✓ 前端依賴已存在
)

echo.
echo [4/5] 啟動 API 服務器...
echo API 將在 http://localhost:8080 運行
start "API Server" cmd /k "cd /d C:\hbgm001\api && .venv\Scripts\activate.bat && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo [5/5] 啟動前端開發服務器...
echo 前端將在 http://localhost:3001 運行
start "Frontend Dev Server" cmd /k "cd /d C:\hbgm001\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   本地開發環境已啟動！
echo ========================================
echo.
echo 服務地址：
echo   🌐 前端: http://localhost:3001
echo   🔧 API:  http://localhost:8080
echo   📚 API 文檔: http://localhost:8080/docs
echo.
echo 測試步驟：
echo   1. 訪問 http://localhost:3001
echo   2. 進入 Wallet 頁面
echo   3. 點擊「發紅包」按鈕
echo   4. 檢查遊戲規則彈窗是否自動顯示
echo   5. 檢查「✨ 遊戲規則 ✨」按鈕
echo.
echo 停止服務：
echo   關閉打開的命令窗口即可停止服務
echo.
pause
