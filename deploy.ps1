# PowerShell 部署腳本 - 上傳到服務器並部署

param(
    [string]$Server = "ubuntu@165.154.254.99",
    [string]$RemotePath = "/opt/luckyred"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LuckyRed 部署腳本 (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Git 操作（帶錯誤處理）
Write-Host "`n[1/4] Git 操作..." -ForegroundColor Green
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
    $commitMsg = Read-Host "輸入提交信息 (直接回車使用默認)"
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    
    Write-Host "提交修改..." -ForegroundColor Yellow
    git commit -m $commitMsg
    if ($LASTEXITCODE -ne 0) {
        # 檢查是否因為沒有變更而失敗
        $statusAfterAdd = git status --porcelain
        if (-not $statusAfterAdd) {
            Write-Host "⚠️  沒有需要提交的變更（可能所有文件都在 .gitignore 中）" -ForegroundColor Yellow
        } else {
            Write-Host "❌ 提交失敗" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ 提交成功: $commitMsg" -ForegroundColor Green
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

# 2. SSH 到服務器拉取代碼
Write-Host "`n[2/4] 連接服務器..." -ForegroundColor Green
$sshCommands = @"
cd $RemotePath
git pull
cd frontend && npm install && npm run build
sudo systemctl restart luckyred-api luckyred-bot luckyred-admin
sudo systemctl status luckyred-api luckyred-bot luckyred-admin --no-pager
"@

ssh $Server $sshCommands

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "MiniApp: https://mini.usdt2026.cc"
Write-Host "Admin: https://admin.usdt2026.cc"

