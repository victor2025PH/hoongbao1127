@echo off
chcp 65001 >nul
echo 正在執行完整部署...
echo.

cd /d C:\hbgm001

echo [1] 添加關鍵文件...
git add api/routers/chats.py api/main.py
if %errorlevel% neq 0 (
    echo ❌ 添加文件失敗
    pause
    exit /b 1
)
echo ✅ 文件已添加
echo.

echo [2] 提交更改...
git commit -m "fix: 添加群組搜索 API 並改進搜索邏輯"
if %errorlevel% neq 0 (
    echo ⚠️  沒有新更改或提交失敗
) else (
    echo ✅ 提交成功
)
echo.

echo [3] 推送到 GitHub...
git push origin master
if %errorlevel% neq 0 (
    echo ❌ 推送失敗！
    pause
    exit /b 1
)
echo ✅ 已推送到 GitHub
echo.

echo [4] 顯示最新提交...
git log --oneline -1
echo.

echo [5] 驗證文件已提交...
git ls-files api/routers/chats.py
if %errorlevel% equ 0 (
    echo ✅ chats.py 已提交
) else (
    echo ❌ chats.py 未提交
)
echo.

echo ========================================
echo   ✅ 本地部署完成！
echo ========================================
echo.
echo 下一步：在服務器上執行更新
pause

