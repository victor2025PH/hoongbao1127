# 快速部署腳本 - 連接到服務器並更新
param(
    [string]$Server = "ubuntu@165.154.254.99",
    [string]$RemotePath = "/opt/luckyred"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LuckyRed 快速部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 檢查本地 Git 狀態
Write-Host "`n[1/5] 檢查本地 Git 狀態..." -ForegroundColor Yellow
Set-Location "C:\hbgm001"
$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "發現未提交的更改：" -ForegroundColor Red
    Write-Host $gitStatus
    $continue = Read-Host "是否繼續部署？(y/n)"
    if ($continue -ne "y") {
        Write-Host "部署已取消" -ForegroundColor Red
        exit
    }
}

# 確認代碼已推送
Write-Host "`n[2/5] 確認代碼已推送到 GitHub..." -ForegroundColor Yellow
$lastCommit = git log -1 --oneline
Write-Host "最新提交: $lastCommit" -ForegroundColor Green

# 構建部署命令
Write-Host "`n[3/5] 準備部署命令..." -ForegroundColor Yellow
$deployScript = @"
#!/bin/bash
set -e
cd $RemotePath
echo '========================================'
echo '  開始部署...'
echo '========================================'
echo ''
echo '[1/4] 拉取最新代碼...'
git fetch origin
git reset --hard origin/master
echo ''
echo '[2/4] 構建前端...'
cd frontend
npm install --silent
npm run build
echo ''
echo '[3/4] 重啟服務...'
sudo systemctl restart luckyred-api luckyred-bot luckyred-admin
echo ''
echo '[4/4] 檢查服務狀態...'
echo ''
echo '--- API 狀態 ---'
sudo systemctl status luckyred-api --no-pager | head -5
echo ''
echo '--- Bot 狀態 ---'
sudo systemctl status luckyred-bot --no-pager | head -5
echo ''
echo '--- Admin 狀態 ---'
sudo systemctl status luckyred-admin --no-pager | head -5
echo ''
echo '========================================'
echo '  部署完成！'
echo '========================================'
"@

# 執行部署
Write-Host "`n[4/5] 連接到服務器並執行部署..." -ForegroundColor Green
Write-Host "服務器: $Server" -ForegroundColor Cyan
Write-Host "路徑: $RemotePath" -ForegroundColor Cyan
Write-Host ""

try {
    # 將腳本寫入臨時文件並執行
    $tempScript = [System.IO.Path]::GetTempFileName()
    $deployScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    # 使用 SSH 執行部署腳本
    ssh $Server "bash -s" < $tempScript
    
    # 清理臨時文件
    Remove-Item $tempScript -Force
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  部署完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "MiniApp: https://mini.usdt2026.cc" -ForegroundColor Cyan
    Write-Host "Admin: https://admin.usdt2026.cc" -ForegroundColor Cyan
} catch {
    Write-Host "`n部署失敗: $_" -ForegroundColor Red
    exit 1
}
