@echo off
chcp 65001 >nul
title 推送代碼到 GitHub

echo ================================================
echo    推送代碼到 GitHub
echo ================================================
echo.

cd /d "c:\hbgm001"

echo [1/4] 檢查 Git 狀態...
git status
echo.

echo [2/4] 添加所有更改...
git add -A
echo.

echo [3/4] 提交更改...
git commit -m "fix: TypeScript type conversion for InviteStats"
echo.

echo [4/4] 推送到 GitHub...
git push origin master
echo.

echo ================================================
echo    完成！請查看上方輸出確認是否成功
echo ================================================
echo.
pause
