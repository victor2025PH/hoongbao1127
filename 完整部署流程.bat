@echo off
chcp 65001 >nul
echo ========================================
echo   完整部署流程 - 一次性執行所有操作
echo ========================================
echo.

cd /d C:\hbgm001

echo [1/5] 檢查 Git 狀態...
git status --short
echo.

echo [2/5] 本地構建測試（檢查所有錯誤）...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo ❌ 構建失敗！請先修復錯誤再繼續
    pause
    exit /b 1
)
cd ..
echo ✅ 本地構建成功
echo.

echo [3/5] 添加所有修改的文件...
git add -A
git status --short
echo.

echo [4/5] 提交所有更改...
set /p commit_msg="請輸入提交信息（直接回車使用默認）: "
if "%commit_msg%"=="" set commit_msg=fix: 修復所有錯誤並更新代碼
git commit -m "%commit_msg%"
echo.

echo [5/5] 推送到 GitHub...
git push origin master
if %errorlevel% neq 0 (
    echo.
    echo ❌ 推送失敗！請檢查認證設置
    pause
    exit /b 1
)
echo.

echo ========================================
echo   ✅ 本地操作完成！
echo ========================================
echo.
echo 下一步：在服務器上執行部署腳本
echo   或執行：ssh ubuntu@165.154.254.99 "bash -s" ^< 服務器部署.sh
echo.
pause

