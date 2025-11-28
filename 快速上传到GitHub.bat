@echo off
chcp 65001 >nul
echo ========================================
echo   上傳修復文件到 GitHub
echo ========================================
echo.

cd /d C:\hbgm001

echo 1. 檢查 Git 狀態...
git status --short

echo.
echo 2. 添加修復的文件...
git add frontend/src/pages/SendRedPacket.tsx
git add frontend/src/providers/I18nProvider.tsx

echo.
echo 3. 提交更改...
git commit -m "fix: 修復 TypeScript 編譯錯誤 - bomb_number 類型和 view_rules 重複問題"

echo.
echo 4. 推送到 GitHub...
echo    注意：如果提示需要認證，請使用 Personal Access Token
git push origin master

echo.
echo ========================================
echo   完成！請檢查 GitHub 倉庫確認上傳成功
echo ========================================
pause

