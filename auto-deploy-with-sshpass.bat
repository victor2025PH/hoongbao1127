@echo off
chcp 65001 >nul
echo ========================================
echo   全自動部署（使用 sshpass）
echo ========================================
echo.

set SERVER=ubuntu@165.154.254.99
set PASSWORD=Along2025!!!
set REMOTE_PATH=/opt/luckyred

REM 檢查 sshpass
where sshpass >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] 未找到 sshpass 工具
    echo 請安裝 sshpass:
    echo   1. 使用 WSL: sudo apt-get install sshpass
    echo   2. 或使用 Git Bash
    echo   3. 或下載: https://github.com/keimpx/sshpass-windows
    pause
    exit /b 1
)

set SSHPASS=%PASSWORD%

echo [1/7] 檢查當前狀態...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "cd %REMOTE_PATH% && pwd && git log --oneline -1"
echo.

echo [2/7] 拉取最新代碼...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "cd %REMOTE_PATH% && git pull origin master"
if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] Git pull 失敗
    pause
    exit /b 1
)
echo [成功] 代碼更新完成
echo.

echo [3/7] 更新 Bot Token...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "cd %REMOTE_PATH% && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && grep BOT_TOKEN .env"
echo [成功] Bot Token 已更新
echo.

echo [4/7] 重啟 API 服務...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api"
echo [成功] API 服務已重啟
echo.

echo [5/7] 重啟 Bot 服務...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot"
echo [成功] Bot 服務已重啟
echo.

echo [6/7] 構建前端（這可能需要幾分鐘）...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "cd %REMOTE_PATH%/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -15"
if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] 前端構建失敗
    pause
    exit /b 1
)
echo [成功] 前端構建完成
echo.

echo [7/7] 重載 Nginx...
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "sudo systemctl reload nginx"
echo [成功] Nginx 已重載
echo.

echo ========================================
echo   部署完成！
echo ========================================
echo.
echo 服務狀態:
sshpass -e ssh -o StrictHostKeyChecking=no %SERVER% "echo Bot: && sudo systemctl is-active luckyred-bot && echo API: && sudo systemctl is-active luckyred-api && echo Nginx: && sudo systemctl is-active nginx"
echo.
pause

