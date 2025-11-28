@echo off
chcp 65001 >nul
echo ========================================
echo   服務器更新代碼並重啟 API 服務
echo ========================================
echo.

echo 正在連接到服務器並執行更新...
echo.

ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && echo '' && echo '✅ 代碼已更新' && echo '' && echo '最新提交:' && git log --oneline -1 && echo '' && echo '重啟 API 服務...' && sudo systemctl restart luckyred-api && sleep 2 && echo '✅ API 服務已重啟' && echo '' && echo '服務狀態:' && sudo systemctl status luckyred-api --no-pager | head -15"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 更新失敗！
    echo 請手動執行以下命令：
    echo   ssh ubuntu@165.154.254.99
    echo   cd /opt/luckyred
    echo   git pull origin master
    echo   sudo systemctl restart luckyred-api
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ 更新完成！
echo ========================================
pause

