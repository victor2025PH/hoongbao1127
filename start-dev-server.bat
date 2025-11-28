@echo off
chcp 65001 >nul
echo ==========================================
echo   啟動前端開發服務器
echo ==========================================
cd frontend
echo 當前目錄: %CD%
echo.
echo 檢查 Node.js...
node --version
echo.
echo 檢查依賴...
if not exist "node_modules" (
    echo 正在安裝依賴...
    call npm install
)
echo.
echo 正在啟動開發服務器...
echo 服務器將在 http://localhost:3001 運行
echo.
echo 按 Ctrl+C 停止服務器
echo ==========================================
echo.
call npm run dev
pause

