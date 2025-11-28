@echo off
chcp 65001
title 修復群組搜索問題

echo ========================================
echo   修復群組搜索問題
echo ========================================
echo.

cd /d C:\hbgm001

echo [步驟 1] 檢查本地代碼...
echo.
git log --oneline -1
git ls-files api/routers/chats.py
if %errorlevel% neq 0 (
    echo [ERROR] chats.py 不在 Git 中
    echo 正在添加...
    git add api/routers/chats.py
    git commit -m "fix: 確保 chats.py 已提交"
    git push origin master
)

echo.
echo [步驟 2] 檢查服務端狀態...
echo 正在連接服務器...
echo.
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && echo '=== 檢查文件 ===' && ls -la api/routers/chats.py 2>&1 && echo '' && echo '=== 檢查路由註冊 ===' && grep -n 'chats' api/main.py 2>&1 && echo '' && echo '=== 當前提交 ===' && git log --oneline -1 2>&1"

echo.
echo [步驟 3] 更新服務端代碼...
echo.
ssh ubuntu@165.154.254.99 "cd /opt/luckyred && git fetch origin && git reset --hard origin/master && echo '✅ 代碼已更新' && git log --oneline -1 && echo '' && echo '=== 驗證文件 ===' && ls -lh api/routers/chats.py 2>&1 && echo '' && echo '=== 檢查搜索函數 ===' && grep -n 'def search_chats' api/routers/chats.py 2>&1"

echo.
echo [步驟 4] 重啟服務...
echo.
ssh ubuntu@165.154.254.99 "sudo systemctl restart luckyred-api && sleep 3 && echo '✅ 服務已重啟' && echo '' && echo '=== 服務狀態 ===' && sudo systemctl is-active luckyred-api && echo '' && echo '=== 服務日誌（最後 10 行）===' && sudo journalctl -u luckyred-api -n 10 --no-pager 2>&1"

echo.
echo [步驟 5] 檢查錯誤日誌...
echo.
ssh ubuntu@165.154.254.99 "sudo journalctl -u luckyred-api -n 30 --no-pager | grep -i 'error\|exception\|traceback\|chats\|search' 2>&1 || echo '未發現相關錯誤'"

echo.
echo ========================================
echo   修復完成
echo ========================================
echo.
echo 請檢查上面的輸出，確認：
echo   1. chats.py 文件存在
echo   2. 路由已正確註冊
echo   3. 服務正常運行
echo   4. 沒有錯誤日誌
echo.
pause

