@echo off
chcp 65001 >nul
echo ========================================
echo   全自動部署 - 完整版
echo ========================================
echo.
echo 正在執行全自動部署腳本...
echo.

powershell -ExecutionPolicy Bypass -File "全自動部署-完整版.ps1"

echo.
echo 按任意鍵退出...
pause >nul

