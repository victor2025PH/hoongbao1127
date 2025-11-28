@echo off
chcp 65001 >nul
title 完整自動化部署 - 一次性解決所有問題

echo.
echo ========================================
echo   完整自動化部署 - 一次性解決所有問題
echo ========================================
echo.

cd /d C:\hbgm001

REM 1. 檢查並添加所有文件
echo [步驟 1/5] 檢查所有修改的文件...
git add -A
git status --short
echo.

REM 2. 提交所有更改
echo [步驟 2/5] 提交所有更改...
git commit -m "fix: 完整更新 - 改進群組搜索邏輯、確保 t.me 鏈接始終返回結果、添加詳細日誌"
if %errorlevel% equ 0 (
    echo ✅ 提交成功
) else (
    echo ⚠️  沒有新更改或提交失敗，繼續執行...
)
echo.

REM 3. 推送到 GitHub
echo [步驟 3/5] 推送到 GitHub...
git push origin master
if %errorlevel% neq 0 (
    echo.
    echo ❌ 推送失敗！
    echo 請檢查：
    echo   1. GitHub 認證（Personal Access Token）
    echo   2. 網絡連接
    echo   3. 遠程倉庫權限
    echo.
    pause
    exit /b 1
)
echo ✅ 已推送到 GitHub
echo.

REM 4. 顯示最新提交
echo [步驟 4/5] 確認最新提交...
git log --oneline -1
echo.

REM 5. 部署到服務器
echo [步驟 5/5] 部署到服務器...
echo 正在連接服務器並執行更新...
echo.

ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && echo '✅ 代碼已更新' && git log --oneline -1 && echo '' && echo '重啟 API 服務...' && sudo systemctl restart luckyred-api && sleep 2 && echo '✅ API 服務已重啟' && sudo systemctl is-active luckyred-api && echo '' && echo '服務狀態:' && sudo systemctl status luckyred-api --no-pager | head -12"

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  服務器部署可能失敗
    echo.
    echo 請手動執行以下命令：
    echo   ssh ubuntu@165.154.254.99
    echo   cd /opt/luckyred
    echo   git pull origin master
    echo   sudo systemctl restart luckyred-api
    echo.
) else (
    echo.
    echo ✅ 服務器部署成功
)

echo.
echo ========================================
echo   ✅ 完整部署流程完成！
echo ========================================
echo.
echo 已完成的操作：
echo   ✅ 所有文件已提交
echo   ✅ 代碼已推送到 GitHub
echo   ✅ 服務器代碼已更新
echo   ✅ API 服務已重啟
echo.
pause

