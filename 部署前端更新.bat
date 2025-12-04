@echo off
chcp 65001 >nul
title 部署前端更新

echo ================================================
echo    部署 MiniApp 前端更新到服務器
echo ================================================
echo.

cd /d "c:\hbgm001"

echo [1/3] 添加所有更改...
git add -A
echo.

echo [2/3] 提交更改...
git commit -m "feat: MiniApp 功能升級 - 紅包真實API、邀請系統、Stars支付、實時餘額、UI優化"
echo.

echo [3/3] 推送到 GitHub...
git push origin master
echo.

echo ================================================
echo    本地 Git 操作完成！
echo ================================================
echo.
echo 接下來請在服務器上執行以下命令：
echo.
echo   ssh ubuntu@165.154.254.99
echo   cd /opt/luckyred
echo   git pull origin master
echo   cd frontend ^&^& npm install ^&^& npm run build
echo   sudo systemctl restart luckyred-api
echo.
echo ================================================
pause
