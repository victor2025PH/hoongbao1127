@echo off
chcp 65001 >nul
echo ========================================
echo   一鍵完整部署 - 本地 + 服務器
echo ========================================
echo.

cd /d C:\hbgm001

echo [本地階段] 開始...
echo.

echo [1/6] 檢查 Git 狀態...
git status --short
echo.

echo [2/6] 本地構建測試...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo ❌ 構建失敗！請先修復錯誤
    pause
    exit /b 1
)
cd ..
echo ✅ 本地構建成功
echo.

echo [3/6] 添加所有修改...
git add -A
echo.

echo [4/6] 提交更改...
set /p commit_msg="提交信息（回車使用默認）: "
if "%commit_msg%"=="" set commit_msg=fix: 自動部署更新
git commit -m "%commit_msg%"
echo.

echo [5/6] 推送到 GitHub...
git push origin master
if %errorlevel% neq 0 (
    echo ❌ 推送失敗！
    pause
    exit /b 1
)
echo ✅ 已推送到 GitHub
echo.

echo [6/6] 部署到服務器...
echo 正在連接到服務器並執行部署...
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && cd frontend && sudo rm -rf dist node_modules/.vite && npm run build && sudo systemctl reload nginx && echo '✅ 部署完成'"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 服務器部署失敗！
    echo 請手動執行：ssh ubuntu@165.154.254.99
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ 完整部署成功！
echo ========================================
pause

