@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   LuckyRed 全自動部署
echo ========================================
echo.

cd /d C:\hbgm001

echo [1/4] 檢查 Git 狀態...
git status --short
echo.

echo [2/4] 檢查未推送的提交...
git log origin/master..HEAD --oneline 2>nul
if %errorlevel% == 0 (
    echo 發現未推送的提交，正在推送...
    git push origin master
)
echo.

echo [3/4] 連接到服務器並部署...
echo 服務器: ubuntu@165.154.254.99
echo.

echo 正在執行部署命令...
echo （如果需要密碼，請輸入 SSH 密碼）
echo.

ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git pull origin master && cd frontend && npm install --silent && npm run build && sudo systemctl restart luckyred-api luckyred-bot luckyred-admin && echo '' && echo '=== 服務狀態 ===' && sudo systemctl status luckyred-api --no-pager | head -8 && sudo systemctl status luckyred-bot --no-pager | head -8"

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo MiniApp: https://mini.usdt2026.cc
echo Admin: https://admin.usdt2026.cc
echo.
pause
