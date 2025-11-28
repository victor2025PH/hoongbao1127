@echo off
chcp 65001 >nul
echo ========================================
echo   上傳 api.ts 到 GitHub
echo ========================================
echo.

cd /d C:\hbgm001

echo 1. 檢查文件狀態...
git status frontend/src/utils/api.ts

echo.
echo 2. 添加 api.ts 文件...
git add frontend/src/utils/api.ts

echo.
echo 3. 提交更改...
git commit -m "fix: 添加缺失的 API 函數 - searchChats, searchUsers, checkUserInChat 和 ChatInfo.link"

echo.
echo 4. 推送到 GitHub...
echo    注意：如果提示需要認證，請使用 Personal Access Token
git push origin master

echo.
echo ========================================
echo   完成！api.ts 已上傳到 GitHub
echo ========================================
echo.
echo 下一步：在服務器上執行：
echo   cd /opt/luckyred
echo   git pull origin master
echo   cd frontend
echo   npm run build
echo.
pause

