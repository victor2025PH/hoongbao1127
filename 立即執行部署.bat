@echo off
chcp 65001
title 全自動部署執行中...

echo ========================================
echo   全自動部署 - 開始執行
echo ========================================
echo.

cd /d C:\hbgm001

echo [步驟 1] 檢查關鍵文件是否在 Git 中...
echo.
git ls-files api/routers/chats.py
if %errorlevel% equ 0 (
    echo [OK] chats.py 已在 Git 中
) else (
    echo [ERROR] chats.py 未在 Git 中
    echo 正在添加...
    git add api/routers/chats.py
    git commit -m "feat: 添加群組搜索 API (chats.py)"
)

git ls-files api/main.py
if %errorlevel% equ 0 (
    echo [OK] main.py 已在 Git 中
) else (
    echo [ERROR] main.py 未在 Git 中
    git add api/main.py
)

echo.
echo [步驟 2] 檢查未提交的更改...
git status --short api/routers/chats.py api/main.py

echo.
echo [步驟 3] 檢查推送狀態...
echo 本地最新提交:
git log --oneline -1
echo.
echo 遠程最新提交:
git log --oneline origin/master -1
echo.

echo [步驟 4] 推送到 GitHub（如果需要）...
git push origin master
echo.

echo [步驟 5] 連接到服務器並檢查文件狀態...
echo 正在連接服務器 165.154.254.99...
echo.
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && echo '=== 當前提交 ===' && git log --oneline -1 && echo '' && echo '=== 檢查關鍵文件 ===' && if [ -f api/routers/chats.py ]; then echo '[OK] api/routers/chats.py 存在' && ls -lh api/routers/chats.py; else echo '[ERROR] api/routers/chats.py 不存在'; fi && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-api 2>&1"
echo.

echo [步驟 6] 執行服務器更新...
echo 正在更新服務器代碼...
echo.
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && echo '[OK] 代碼已更新' && git log --oneline -1 && echo '' && echo '=== 驗證關鍵文件 ===' && if [ -f api/routers/chats.py ]; then echo '[OK] api/routers/chats.py 存在' && ls -lh api/routers/chats.py; else echo '[ERROR] api/routers/chats.py 不存在'; fi && echo '' && echo '=== 重啟 API 服務 ===' && sudo systemctl restart luckyred-api && sleep 3 && echo '[OK] API 服務已重啟' && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-api && echo '' && echo '=== 服務日誌（最後 10 行）===' && sudo journalctl -u luckyred-api -n 10 --no-pager"
echo.

echo ========================================
echo   部署完成
echo ========================================
echo.
echo 請檢查上面的輸出，確認所有步驟都成功執行。
echo.
pause

