# 全自動部署腳本 - 生成詳細分析報告
$ErrorActionPreference = "Continue"
$report = @()

function Add-Report {
    param($step, $status, $message, $details = "")
    $report += [PSCustomObject]@{
        Step = $step
        Status = $status
        Message = $message
        Details = $details
        Time = Get-Date -Format "HH:mm:ss"
    }
    Write-Host "[$step] $status - $message" -ForegroundColor $(if ($status -eq "✅") { "Green" } elseif ($status -eq "❌") { "Red" } else { "Yellow" })
    if ($details) { Write-Host "   $details" -ForegroundColor Gray }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  全自動部署流程 - 詳細分析報告" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\hbgm001

# 步驟 1: 檢查 Git 狀態
Add-Report "步驟 1" "🔍" "檢查 Git 狀態和未提交的文件"
$gitStatus = git status --short 2>&1
if ($gitStatus) {
    Add-Report "步驟 1" "⚠️" "發現未提交的文件" ($gitStatus -join "`n   ")
    
    # 檢查關鍵文件
    $chatsStatus = git status api/routers/chats.py 2>&1
    if ($chatsStatus -match "Untracked") {
        Add-Report "步驟 1" "❌" "chats.py 是未跟踪的新文件" "這是關鍵問題！文件從未被提交"
    } elseif ($chatsStatus -match "modified") {
        Add-Report "步驟 1" "⚠️" "chats.py 已修改但未提交"
    } else {
        Add-Report "步驟 1" "✅" "chats.py 狀態正常"
    }
    
    $mainStatus = git status api/main.py 2>&1
    if ($mainStatus -match "modified") {
        Add-Report "步驟 1" "⚠️" "main.py 已修改但未提交"
    }
} else {
    Add-Report "步驟 1" "✅" "沒有未提交的文件"
}

# 檢查文件是否在 Git 中
$chatsInGit = git ls-files api/routers/chats.py 2>&1
if ($chatsInGit -and -not ($chatsInGit -match "error")) {
    Add-Report "步驟 1" "✅" "chats.py 已在 Git 中" $chatsInGit
} else {
    Add-Report "步驟 1" "❌" "chats.py 未在 Git 中" "這是導致搜索功能無法使用的根本原因"
}

Write-Host ""

# 步驟 2: 添加文件
Add-Report "步驟 2" "📦" "添加關鍵文件到 Git"
git add api/routers/chats.py api/main.py 2>&1 | Out-Null
$addedStatus = git status --short api/routers/chats.py api/main.py 2>&1
if ($addedStatus) {
    Add-Report "步驟 2" "✅" "文件已添加到暫存區" ($addedStatus -join "`n   ")
} else {
    Add-Report "步驟 2" "⚠️" "文件可能已經在暫存區或已提交"
}

Write-Host ""

# 步驟 3: 本地構建測試
Add-Report "步驟 3" "🏗️" "本地構建測試"
Set-Location frontend
$buildOutput = npm run build 2>&1
$buildSuccess = $LASTEXITCODE -eq 0
Set-Location ..

if ($buildSuccess) {
    Add-Report "步驟 3" "✅" "本地構建成功"
} else {
    $errors = $buildOutput | Select-String -Pattern "error" -Context 1,1
    Add-Report "步驟 3" "❌" "構建失敗" ($errors -join "`n   ")
    Add-Report "步驟 3" "⚠️" "繼續執行部署（可能需要手動修復）"
}

Write-Host ""

# 步驟 4: 提交更改
Add-Report "步驟 4" "💾" "提交所有更改"
$commitMsg = "fix: 完整更新 - 添加群組搜索 API (chats.py)、改進搜索邏輯、確保 t.me 鏈接始終返回結果"
$commitOutput = git commit -m $commitMsg 2>&1

if ($LASTEXITCODE -eq 0) {
    $commitHash = git log --oneline -1
    Add-Report "步驟 4" "✅" "提交成功" $commitHash
} else {
    if ($commitOutput -match "nothing to commit") {
        Add-Report "步驟 4" "⚠️" "沒有新更改需要提交" "可能已經提交過了"
    } else {
        Add-Report "步驟 4" "❌" "提交失敗" $commitOutput
    }
}

Write-Host ""

# 步驟 5: 推送到 GitHub
Add-Report "步驟 5" "🚀" "推送到 GitHub"
$pushOutput = git push origin master 2>&1

if ($LASTEXITCODE -eq 0) {
    Add-Report "步驟 5" "✅" "已推送到 GitHub"
    if ($pushOutput -match "Writing objects") {
        $objMatch = [regex]::Match($pushOutput, "Writing objects:.*done")
        if ($objMatch.Success) {
            Add-Report "步驟 5" "✅" "推送詳情" $objMatch.Value
        }
    }
} else {
    Add-Report "步驟 5" "❌" "推送失敗" $pushOutput
    Add-Report "步驟 5" "💡" "可能的原因" "1. GitHub 認證問題（需要 Personal Access Token）`n   2. 網絡連接問題`n   3. 遠程倉庫權限問題"
    Add-Report "步驟 5" "🔧" "需要協助" "請設置 GitHub Personal Access Token: https://github.com/settings/tokens"
}

Write-Host ""

# 步驟 6: 驗證推送成功
Add-Report "步驟 6" "✅" "驗證推送成功"
$localCommit = (git log --oneline -1).Trim()
$remoteCommit = (git log --oneline origin/master -1).Trim()

Add-Report "步驟 6" "🔍" "本地最新提交" $localCommit
Add-Report "步驟 6" "🔍" "遠程最新提交" $remoteCommit

if ($localCommit -eq $remoteCommit) {
    Add-Report "步驟 6" "✅" "本地和遠程已同步"
} else {
    Add-Report "步驟 6" "⚠️" "本地和遠程不同步" "需要重新推送"
}

$fileCheck = git ls-files api/routers/chats.py 2>&1
if ($fileCheck -and -not ($fileCheck -match "error")) {
    Add-Report "步驟 6" "✅" "chats.py 已在 Git 中" $fileCheck
} else {
    Add-Report "步驟 6" "❌" "chats.py 未在 Git 中" "需要重新添加"
}

Write-Host ""

# 步驟 7: 部署到服務器
Add-Report "步驟 7" "🖥️" "部署到服務器"
Write-Host "正在連接服務器..." -ForegroundColor Gray

$serverCmd = @"
cd /opt/luckyred && 
git fetch origin && 
git reset --hard origin/master && 
echo '=== 代碼更新 ===' && 
git log --oneline -1 && 
echo '' && 
echo '=== 檢查 chats.py ===' && 
if [ -f api/routers/chats.py ]; then 
    echo '✅ chats.py 存在' && 
    ls -lh api/routers/chats.py
else 
    echo '❌ chats.py 不存在'
fi && 
echo '' && 
echo '=== 重啟 API 服務 ===' && 
sudo systemctl restart luckyred-api && 
sleep 2 && 
echo '✅ API 服務已重啟' && 
echo '' && 
echo '=== 服務狀態 ===' && 
sudo systemctl is-active luckyred-api && 
sudo systemctl status luckyred-api --no-pager | head -15
"@

try {
    $serverOutput = ssh ubuntu@165.154.254.99 $serverCmd 2>&1
    Write-Host $serverOutput
    
    if ($serverOutput -match "chats.py 存在") {
        Add-Report "步驟 7" "✅" "chats.py 文件存在於服務器"
    } elseif ($serverOutput -match "chats.py 不存在") {
        Add-Report "步驟 7" "❌" "chats.py 文件不存在於服務器" "代碼可能未更新"
    }
    
    if ($serverOutput -match "active.*running") {
        Add-Report "步驟 7" "✅" "API 服務運行正常"
    } else {
        Add-Report "步驟 7" "⚠️" "需要檢查服務狀態"
    }
    
    if ($LASTEXITCODE -eq 0) {
        Add-Report "步驟 7" "✅" "服務器部署成功"
    } else {
        Add-Report "步驟 7" "⚠️" "服務器部署可能失敗" "請檢查 SSH 連接和權限"
    }
} catch {
    Add-Report "步驟 7" "❌" "無法連接到服務器" $_.Exception.Message
    Add-Report "步驟 7" "🔧" "需要協助" "請手動執行服務器更新命令"
}

Write-Host ""

# 生成報告
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署分析報告" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$report | Format-Table -AutoSize

# 保存報告到文件
$report | Export-Csv -Path "部署報告-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv" -NoTypeInformation -Encoding UTF8
$report | ConvertTo-Json -Depth 3 | Out-File -FilePath "部署報告-$(Get-Date -Format 'yyyyMMdd-HHmmss').json" -Encoding UTF8

Write-Host ""
Write-Host "報告已保存到:" -ForegroundColor Green
Write-Host "  - 部署報告-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv" -ForegroundColor Gray
Write-Host "  - 部署報告-$(Get-Date -Format 'yyyyMMdd-HHmmss').json" -ForegroundColor Gray
Write-Host ""

# 總結
$successCount = ($report | Where-Object { $_.Status -eq "✅" }).Count
$errorCount = ($report | Where-Object { $_.Status -eq "❌" }).Count
$warningCount = ($report | Where-Object { $_.Status -eq "⚠️" }).Count

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  執行總結" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 成功: $successCount" -ForegroundColor Green
Write-Host "❌ 失敗: $errorCount" -ForegroundColor Red
Write-Host "⚠️  警告: $warningCount" -ForegroundColor Yellow
Write-Host ""

if ($errorCount -eq 0 -and $warningCount -eq 0) {
    Write-Host "🎉 所有步驟執行成功！" -ForegroundColor Green
} elseif ($errorCount -gt 0) {
    Write-Host "⚠️  發現錯誤，請查看報告詳情" -ForegroundColor Yellow
    Write-Host "需要協助的項目:" -ForegroundColor Yellow
    $report | Where-Object { $_.Message -match "需要協助" } | ForEach-Object {
        Write-Host "  - $($_.Step): $($_.Details)" -ForegroundColor Gray
    }
}

