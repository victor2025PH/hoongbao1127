@echo off
chcp 65001 >nul
echo ========================================
echo   全自動部署 - 開始執行
echo ========================================
echo.

cd /d C:\hbgm001

echo [步驟 1] 檢查關鍵文件是否在 Git 中...
git ls-files api/routers/chats.py
if %errorlevel% equ 0 (
    echo ✅ chats.py 已在 Git 中
) else (
    echo ❌ chats.py 未在 Git 中
)

git ls-files api/main.py
if %errorlevel% equ 0 (
    echo ✅ main.py 已在 Git 中
) else (
    echo ❌ main.py 未在 Git 中
)

echo.
echo [步驟 2] 檢查未提交的更改...
git status --short api/routers/chats.py api/main.py

echo.
echo [步驟 3] 檢查推送狀態...
echo 本地最新提交:
git log --oneline -1
echo 遠程最新提交:
git log --oneline origin/master -1

echo.
echo [步驟 4] 連接到服務器並檢查文件狀態...
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && echo '=== 當前提交 ===' && git log --oneline -1 && echo '' && echo '=== 檢查關鍵文件 ===' && if [ -f api/routers/chats.py ]; then echo '✅ api/routers/chats.py 存在' && ls -lh api/routers/chats.py; else echo '❌ api/routers/chats.py 不存在'; fi && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-api 2>&1"

echo.
echo [步驟 5] 執行服務器更新...
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && echo '✅ 代碼已更新' && git log --oneline -1 && echo '' && echo '=== 驗證關鍵文件 ===' && if [ -f api/routers/chats.py ]; then echo '✅ api/routers/chats.py 存在' && ls -lh api/routers/chats.py; else echo '❌ api/routers/chats.py 不存在'; fi && echo '' && echo '=== 重啟 API 服務 ===' && sudo systemctl restart luckyred-api && sleep 3 && echo '✅ API 服務已重啟' && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-api && echo '' && echo '=== 服務日誌（最後 10 行）===' && sudo journalctl -u luckyred-api -n 10 --no-pager"

echo.
echo ========================================
echo   部署完成
echo ========================================
echo.
pause

