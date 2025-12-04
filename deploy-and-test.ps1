# 全自動部署並測試腳本

param(
    [string]$Server = "ubuntu@165.154.254.99",
    [string]$RemotePath = "/opt/luckyred",
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LuckyRed 全自動部署並測試" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Git 操作
Write-Host "`n[1/5] Git 操作..." -ForegroundColor Green
Set-Location "C:\hbgm001"

# 檢查未提交的修改
Write-Host "檢查未提交的修改..." -ForegroundColor Yellow
$status = git status --porcelain

if ($status) {
    Write-Host "發現未提交的修改：" -ForegroundColor Yellow
    Write-Host $status
    
    # 添加所有修改
    Write-Host "添加所有修改到暫存區..." -ForegroundColor Yellow
    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ git add 失敗" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 所有修改已添加到暫存區" -ForegroundColor Green
    
    # 提交
    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        $CommitMessage = "chore: 自動部署 - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    
    Write-Host "提交修改: $CommitMessage" -ForegroundColor Yellow
    git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        $statusAfterAdd = git status --porcelain
        if (-not $statusAfterAdd) {
            Write-Host "⚠️  沒有需要提交的變更" -ForegroundColor Yellow
        } else {
            Write-Host "❌ 提交失敗" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ 提交成功" -ForegroundColor Green
    }
} else {
    Write-Host "✓ 沒有未提交的修改" -ForegroundColor Green
}

# 檢查未推送的提交
Write-Host "`n檢查未推送的提交..." -ForegroundColor Yellow
$unpushed = git log origin/master..HEAD --oneline 2>$null

if ($unpushed) {
    Write-Host "發現未推送的提交：" -ForegroundColor Yellow
    Write-Host $unpushed
    Write-Host "推送到 GitHub..." -ForegroundColor Yellow
    git push origin master
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ git push 失敗" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 推送成功" -ForegroundColor Green
} else {
    Write-Host "✓ 所有提交已推送到 GitHub" -ForegroundColor Green
}

# 2. 部署到服務器
Write-Host "`n[2/5] 部署到服務器..." -ForegroundColor Green
$sshCommands = @"
cd $RemotePath && \
echo '=== 拉取最新代碼 ===' && \
git pull origin master && \
echo '' && \
echo '=== 清除構建緩存 ===' && \
cd frontend && \
rm -rf node_modules/.vite dist && \
echo '' && \
echo '=== 重新構建前端 ===' && \
npm install --silent && \
npm run build && \
echo '' && \
echo '=== 重啟服務 ===' && \
sudo systemctl restart luckyred-api luckyred-bot luckyred-admin && \
sudo systemctl reload nginx && \
echo '' && \
echo '=== 檢查服務狀態 ===' && \
sudo systemctl is-active luckyred-api && echo 'API: 運行中' || echo 'API: 未運行' && \
sudo systemctl is-active luckyred-bot && echo 'Bot: 運行中' || echo 'Bot: 未運行' && \
sudo systemctl is-active luckyred-admin && echo 'Admin: 運行中' || echo 'Admin: 未運行'
"@

try {
    ssh $Server $sshCommands
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 服務器部署失敗" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ SSH 連接失敗: $_" -ForegroundColor Red
    exit 1
}

# 3. 檢查服務狀態
Write-Host "`n[3/5] 檢查服務狀態..." -ForegroundColor Green
$statusCheck = ssh $Server "sudo systemctl status luckyred-api --no-pager | head -10 && echo '' && sudo systemctl status luckyred-bot --no-pager | head -10"
Write-Host $statusCheck

# 4. 檢查構建文件
Write-Host "`n[4/5] 檢查構建文件..." -ForegroundColor Green
$buildCheck = ssh $Server "ls -lh $RemotePath/frontend/dist/assets/ | grep SendRedPacket | head -1"
Write-Host $buildCheck

# 5. 測試結果
Write-Host "`n[5/5] 部署測試結果..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "請訪問以下網址測試：" -ForegroundColor Cyan
Write-Host "  MiniApp: https://mini.usdt2026.cc" -ForegroundColor Yellow
Write-Host "  Admin: https://admin.usdt2026.cc" -ForegroundColor Yellow
Write-Host ""
Write-Host "測試重點：" -ForegroundColor Cyan
Write-Host "  1. 進入「發送紅包」頁面" -ForegroundColor White
Write-Host "  2. 確認遊戲規則彈窗自動顯示" -ForegroundColor White
Write-Host "  3. 檢查「✨ 遊戲規則 ✨」按鈕" -ForegroundColor White
Write-Host "  4. 測試「以後不再彈出」選項" -ForegroundColor White
Write-Host ""
