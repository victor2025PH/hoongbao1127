# 完整部署流程 - 一次性執行所有操作
# 使用方法：.\完整部署流程.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完整部署流程 - 一次性執行所有操作" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\hbgm001

# 1. 檢查 Git 狀態
Write-Host "[1/5] 檢查 Git 狀態..." -ForegroundColor Yellow
git status --short
Write-Host ""

# 2. 本地構建測試
Write-Host "[2/5] 本地構建測試（檢查所有錯誤）..." -ForegroundColor Yellow
Set-Location frontend
$buildResult = npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 構建失敗！請先修復錯誤再繼續" -ForegroundColor Red
    Set-Location ..
    Read-Host "按 Enter 退出"
    exit 1
}
Set-Location ..
Write-Host "✅ 本地構建成功" -ForegroundColor Green
Write-Host ""

# 3. 添加所有修改的文件
Write-Host "[3/5] 添加所有修改的文件..." -ForegroundColor Yellow
git add -A
git status --short
Write-Host ""

# 4. 提交所有更改
Write-Host "[4/5] 提交所有更改..." -ForegroundColor Yellow
$commitMsg = Read-Host "請輸入提交信息（直接回車使用默認）"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "fix: 修復所有錯誤並更新代碼"
}
git commit -m $commitMsg
Write-Host ""

# 5. 推送到 GitHub
Write-Host "[5/5] 推送到 GitHub..." -ForegroundColor Yellow
git push origin master
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 推送失敗！請檢查認證設置" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 本地操作完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：在服務器上執行部署腳本" -ForegroundColor Yellow
Write-Host "  或執行：ssh ubuntu@165.154.254.99 'bash -s' < 服務器部署.sh" -ForegroundColor Gray
Write-Host ""

