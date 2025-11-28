@echo off
chcp 65001 >nul
echo ==========================================
echo   自動啟動並測試開發服務器
echo ==========================================
echo.

cd /d "%~dp0frontend"

echo [1] 檢查環境...
node --version
npm --version
echo.

echo [2] 安裝依賴（如果需要）...
if not exist "node_modules" (
    call npm install
)
echo.

echo [3] 啟動開發服務器...
echo 服務器將在 http://localhost:3001 運行
echo.
start "Vite Dev Server" cmd /k "npm run dev"

echo [4] 等待服務器啟動...
timeout /t 15 /nobreak >nul

echo [5] 檢查服務器狀態...
netstat -ano | findstr ":3001" >nul
if errorlevel 1 (
    echo [錯誤] 服務器未啟動
    pause
    exit /b 1
) else (
    echo [成功] 服務器已啟動
    echo.
    echo [6] 打開瀏覽器...
    start http://localhost:3001
    echo.
    echo 服務器正在運行，瀏覽器已打開
    echo 按任意鍵關閉此窗口（服務器將繼續運行）
    pause >nul
)

