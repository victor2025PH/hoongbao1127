# 全自動部署腳本 - 完整版
# 包含：自動檢查關鍵文件、自動驗證服務器狀態、自動執行服務器更新

$ErrorActionPreference = "Continue"
$report = @()
$serverIP = "165.154.254.99"
$serverUser = "ubuntu"
$criticalFiles = @(
    "api/routers/chats.py",
    "api/main.py"
)

function Add-Report {
    param($step, $status, $message, $details = "", $needsHelp = $false)
    $report += [PSCustomObject]@{
        Step = $step
        Status = $status
        Message = $message
        Details = $details
        NeedsHelp = $needsHelp
        Time = Get-Date -Format "HH:mm:ss"
    }
    $color = switch ($status) {
        "✅" { "Green" }
        "❌" { "Red" }
        "⚠️" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "[$step] $status - $message" -ForegroundColor $color
    if ($details) { Write-Host "   $details" -ForegroundColor Gray }
    if ($needsHelp) { Write-Host "   ⚠️ 需要協助" -ForegroundColor Yellow }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  全自動部署 - 完整版" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\hbgm001

# ========================================
# 步驟 1: 自動檢查關鍵文件是否在 Git 中
# ========================================
Add-Report "步驟 1" "🔍" "自動檢查關鍵文件是否在 Git 中"

$filesToCommit = @()
$filesInGit = @()
$filesNotInGit = @()

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        $inGit = git ls-files $file 2>&1
        if ($inGit -and -not ($inGit -match "error|fatal")) {
            $filesInGit += $file
            Add-Report "步驟 1" "✅" "$file 已在 Git 中" $inGit
        } else {
            $filesNotInGit += $file
            $filesToCommit += $file
            Add-Report "步驟 1" "❌" "$file 未在 Git 中" "需要添加"
        }
    } else {
        Add-Report "步驟 1" "❌" "$file 文件不存在" "請檢查文件路徑"
    }
}

# 檢查是否有未提交的更改
Add-Report "步驟 1" "🔍" "檢查未提交的更改"
$uncommitted = git status --short $criticalFiles 2>&1
if ($uncommitted) {
    Add-Report "步驟 1" "⚠️" "發現未提交的更改" ($uncommitted -join "`n   ")
    $filesToCommit += ($uncommitted | ForEach-Object { ($_ -split '\s+')[1] } | Where-Object { $_ -in $criticalFiles })
}

Write-Host ""

# ========================================
# 步驟 2: 自動添加並提交關鍵文件
# ========================================
if ($filesToCommit.Count -gt 0) {
    Add-Report "步驟 2" "📦" "自動添加並提交關鍵文件"
    
    $filesToCommit = $filesToCommit | Select-Object -Unique
    foreach ($file in $filesToCommit) {
        git add $file 2>&1 | Out-Null
        Add-Report "步驟 2" "✅" "已添加 $file"
    }
    
    $commitMsg = "fix: 自動提交關鍵文件 - $(($filesToCommit -join ', '))"
    $commitOutput = git commit -m $commitMsg 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $commitHash = (git log --oneline -1).Trim()
        Add-Report "步驟 2" "✅" "提交成功" $commitHash
    } else {
        if ($commitOutput -match "nothing to commit") {
            Add-Report "步驟 2" "⚠️" "沒有新更改需要提交"
        } else {
            Add-Report "步驟 2" "❌" "提交失敗" $commitOutput $true
        }
    }
} else {
    Add-Report "步驟 2" "✅" "所有關鍵文件已在 Git 中，無需提交"
}

Write-Host ""

# ========================================
# 步驟 3: 本地構建測試
# ========================================
Add-Report "步驟 3" "🏗️" "本地構建測試"
Set-Location frontend
$buildOutput = npm run build 2>&1
$buildSuccess = $LASTEXITCODE -eq 0
Set-Location ..

if ($buildSuccess) {
    Add-Report "步驟 3" "✅" "本地構建成功"
} else {
    $errors = $buildOutput | Select-String -Pattern "error" -Context 1,1
    Add-Report "步驟 3" "⚠️" "構建失敗（繼續執行）" ($errors -join "`n   ")
}

Write-Host ""

# ========================================
# 步驟 4: 推送到 GitHub
# ========================================
Add-Report "步驟 4" "🚀" "推送到 GitHub"
$pushOutput = git push origin master 2>&1

if ($LASTEXITCODE -eq 0) {
    Add-Report "步驟 4" "✅" "已推送到 GitHub"
    if ($pushOutput -match "Writing objects") {
        $objMatch = [regex]::Match($pushOutput, "Writing objects:.*done")
        if ($objMatch.Success) {
            Add-Report "步驟 4" "✅" "推送詳情" $objMatch.Value
        }
    }
} else {
    Add-Report "步驟 4" "❌" "推送失敗" $pushOutput $true
    Add-Report "步驟 4" "💡" "可能的原因" "1. GitHub 認證問題`n   2. 網絡連接問題`n   3. 遠程倉庫權限問題" $true
}

Write-Host ""

# ========================================
# 步驟 5: 驗證推送成功
# ========================================
Add-Report "步驟 5" "✅" "驗證推送成功"
$localCommit = (git log --oneline -1).Trim()
$remoteCommit = (git log --oneline origin/master -1).Trim()

Add-Report "步驟 5" "🔍" "本地最新提交" $localCommit
Add-Report "步驟 5" "🔍" "遠程最新提交" $remoteCommit

if ($localCommit -eq $remoteCommit) {
    Add-Report "步驟 5" "✅" "本地和遠程已同步"
} else {
    Add-Report "步驟 5" "❌" "本地和遠程不同步" "需要重新推送" $true
}

# 驗證關鍵文件
foreach ($file in $criticalFiles) {
    $inGit = git ls-files $file 2>&1
    if ($inGit -and -not ($inGit -match "error|fatal")) {
        Add-Report "步驟 5" "✅" "$file 已在 Git 中" $inGit
    } else {
        Add-Report "步驟 5" "❌" "$file 未在 Git 中" "需要重新添加" $true
    }
}

Write-Host ""

# ========================================
# 步驟 6: 自動驗證服務器文件狀態
# ========================================
Add-Report "步驟 6" "🖥️" "自動驗證服務器文件狀態"

Write-Host "正在連接服務器 $serverUser@$serverIP ..." -ForegroundColor Gray

$checkServerCmd = @"
cd /opt/luckyred && 
echo '=== 當前提交 ===' && 
git log --oneline -1 && 
echo '' && 
echo '=== 檢查關鍵文件 ===' && 
$(foreach ($file in $criticalFiles) {
    "if [ -f $file ]; then echo '✅ $file 存在' && ls -lh $file; else echo '❌ $file 不存在'; fi && echo '';"
}) 
echo '=== 服務狀態 ===' && 
sudo systemctl is-active luckyred-api 2>&1
"@

try {
    $serverCheckOutput = ssh ${serverUser}@${serverIP} $checkServerCmd 2>&1
    Write-Host $serverCheckOutput
    
    # 分析服務器狀態
    foreach ($file in $criticalFiles) {
        if ($serverCheckOutput -match "$file 存在") {
            Add-Report "步驟 6" "✅" "服務器上 $file 存在"
        } elseif ($serverCheckOutput -match "$file 不存在") {
            Add-Report "步驟 6" "❌" "服務器上 $file 不存在" "需要更新代碼" $true
        }
    }
    
    if ($serverCheckOutput -match "active.*running") {
        Add-Report "步驟 6" "✅" "API 服務運行正常"
    } else {
        Add-Report "步驟 6" "⚠️" "API 服務狀態異常" "需要檢查" $true
    }
} catch {
    Add-Report "步驟 6" "❌" "無法連接到服務器" $_.Exception.Message $true
}

Write-Host ""

# ========================================
# 步驟 7: 自動執行服務器更新
# ========================================
Add-Report "步驟 7" "🔄" "自動執行服務器更新"

$updateServerCmd = @"
cd /opt/luckyred && 
echo '=== 更新代碼 ===' && 
git fetch origin && 
git reset --hard origin/master && 
echo '✅ 代碼已更新' && 
git log --oneline -1 && 
echo '' && 
echo '=== 驗證關鍵文件 ===' && 
$(foreach ($file in $criticalFiles) {
    "if [ -f $file ]; then echo '✅ $file 存在' && ls -lh $file; else echo '❌ $file 不存在'; fi && echo '';"
}) 
echo '=== 重啟 API 服務 ===' && 
sudo systemctl restart luckyred-api && 
sleep 3 && 
echo '✅ API 服務已重啟' && 
echo '' && 
echo '=== 服務狀態 ===' && 
sudo systemctl is-active luckyred-api && 
echo '' && 
echo '=== 服務日誌（最後 10 行）===' && 
sudo journalctl -u luckyred-api -n 10 --no-pager
"@

try {
    $serverUpdateOutput = ssh ${serverUser}@${serverIP} $updateServerCmd 2>&1
    Write-Host $serverUpdateOutput
    
    # 分析更新結果
    if ($serverUpdateOutput -match "代碼已更新") {
        Add-Report "步驟 7" "✅" "服務器代碼已更新"
    } else {
        Add-Report "步驟 7" "⚠️" "服務器代碼更新可能失敗" "請檢查輸出" $true
    }
    
    foreach ($file in $criticalFiles) {
        if ($serverUpdateOutput -match "$file 存在") {
            Add-Report "步驟 7" "✅" "服務器上 $file 存在"
        } elseif ($serverUpdateOutput -match "$file 不存在") {
            Add-Report "步驟 7" "❌" "服務器上 $file 不存在" "需要手動檢查" $true
        }
    }
    
    if ($serverUpdateOutput -match "active.*running") {
        Add-Report "步驟 7" "✅" "API 服務運行正常"
    } else {
        Add-Report "步驟 7" "❌" "API 服務啟動失敗" "需要查看日誌" $true
    }
    
    # 檢查是否有錯誤日誌
    if ($serverUpdateOutput -match "error|Error|ERROR|failed|Failed|FAILED") {
        $errors = $serverUpdateOutput | Select-String -Pattern "error|Error|ERROR|failed|Failed|FAILED" -Context 1,1
        Add-Report "步驟 7" "⚠️" "發現錯誤日誌" ($errors -join "`n   ") $true
    }
    
} catch {
    Add-Report "步驟 7" "❌" "服務器更新失敗" $_.Exception.Message $true
}

Write-Host ""

# ========================================
# 生成報告
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署分析報告" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$report | Format-Table -AutoSize

# 保存報告
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$csvPath = "部署報告-$timestamp.csv"
$jsonPath = "部署報告-$timestamp.json"
$mdPath = "部署報告-$timestamp.md"

$report | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
$report | ConvertTo-Json -Depth 3 | Out-File -FilePath $jsonPath -Encoding UTF8

# 生成 Markdown 報告
$mdContent = @"
# 部署分析報告

**生成時間**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## 執行總結

| 步驟 | 狀態 | 說明 |
|------|------|------|
"@

foreach ($item in $report) {
    $mdContent += "`n| $($item.Step) | $($item.Status) | $($item.Message) |"
}

$mdContent += @"

## 詳細信息

"@

foreach ($item in $report) {
    $mdContent += @"

### $($item.Step) - $($item.Status) $($item.Message)

**時間**: $($item.Time)

$($item.Details)

"@
    if ($item.NeedsHelp) {
        $mdContent += "**⚠️ 需要協助**`n`n"
    }
}

$mdContent | Out-File -FilePath $mdPath -Encoding UTF8

Write-Host ""
Write-Host "報告已保存到:" -ForegroundColor Green
Write-Host "  - $csvPath" -ForegroundColor Gray
Write-Host "  - $jsonPath" -ForegroundColor Gray
Write-Host "  - $mdPath" -ForegroundColor Gray
Write-Host ""

# 總結
$successCount = ($report | Where-Object { $_.Status -eq "✅" }).Count
$errorCount = ($report | Where-Object { $_.Status -eq "❌" }).Count
$warningCount = ($report | Where-Object { $_.Status -eq "⚠️" }).Count
$needsHelpCount = ($report | Where-Object { $_.NeedsHelp -eq $true }).Count

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  執行總結" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 成功: $successCount" -ForegroundColor Green
Write-Host "❌ 失敗: $errorCount" -ForegroundColor Red
Write-Host "⚠️  警告: $warningCount" -ForegroundColor Yellow
if ($needsHelpCount -gt 0) {
    Write-Host "🔧 需要協助: $needsHelpCount" -ForegroundColor Yellow
}
Write-Host ""

if ($errorCount -eq 0 -and $warningCount -eq 0) {
    Write-Host "🎉 所有步驟執行成功！" -ForegroundColor Green
} elseif ($errorCount -gt 0) {
    Write-Host "⚠️  發現錯誤，請查看報告詳情" -ForegroundColor Yellow
    Write-Host "需要協助的項目:" -ForegroundColor Yellow
    $report | Where-Object { $_.NeedsHelp -eq $true } | ForEach-Object {
        Write-Host "  - $($_.Step): $($_.Message)" -ForegroundColor Gray
    }
}

