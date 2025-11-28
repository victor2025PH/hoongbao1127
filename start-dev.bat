@echo off
echo ==========================================
echo   啟動前端開發服務器
echo ==========================================
cd frontend
echo 當前目錄: %CD%
echo.
echo 正在啟動開發服務器...
echo 服務器將在 http://localhost:3001 運行
echo.
echo 按 Ctrl+C 停止服務器
echo ==========================================
echo.
npm run dev
pause

