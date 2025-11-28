@echo off
chcp 65001 >nul
echo ========================================
echo   全自動部署到服務器
echo ========================================
echo.
echo 服務器: ubuntu@165.154.254.99
echo.
echo 提示: 如果需要輸入 SSH 密碼，請在提示時輸入
echo.

set SERVER=ubuntu@165.154.254.99
set REMOTE_PATH=/opt/luckyred

echo [1/7] 檢查當前狀態...
ssh %SERVER% "cd %REMOTE_PATH% && pwd && git log --oneline -1 && git status --short"
echo.

echo [2/7] 拉取最新代碼...
ssh %SERVER% "cd %REMOTE_PATH% && git pull origin master"
if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] Git pull 失敗
    pause
    exit /b 1
)
echo [成功] 代碼更新完成
echo.

echo [3/7] 更新 Bot Token...
ssh %SERVER% "cd %REMOTE_PATH% && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && grep BOT_TOKEN .env"
echo [成功] Bot Token 已更新
echo.

echo [4/7] 重啟 API 服務...
ssh %SERVER% "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api"
echo [成功] API 服務已重啟
echo.

echo [5/7] 重啟 Bot 服務...
ssh %SERVER% "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot"
echo [成功] Bot 服務已重啟
echo.

echo [6/7] 構建前端（這可能需要幾分鐘）...
ssh %SERVER% "cd %REMOTE_PATH%/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -15"
if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] 前端構建失敗
    pause
    exit /b 1
)
echo [成功] 前端構建完成
echo.

echo [7/7] 重載 Nginx...
ssh %SERVER% "sudo systemctl reload nginx"
echo [成功] Nginx 已重載
echo.

echo ========================================
echo   部署完成！
echo ========================================
echo.
echo 服務狀態:
ssh %SERVER% "echo Bot: && sudo systemctl is-active luckyred-bot && echo API: && sudo systemctl is-active luckyred-api && echo Nginx: && sudo systemctl is-active nginx"
echo.
pause

