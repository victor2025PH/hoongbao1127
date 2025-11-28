# 完整自動化部署腳本 - 顯示詳細輸出
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完整自動化部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\hbgm001

# 1. 添加文件
Write-Host "[1/6] 添加關鍵文件..." -ForegroundColor Yellow
git add api/routers/chats.py api/main.py
$status = git status --short api/routers/chats.py api/main.py
if ($status) {
    Write-Host $status -ForegroundColor Green
    Write-Host "✅ 文件已添加到暫存區" -ForegroundColor Green
} else {
    Write-Host "⚠️  文件可能已經在暫存區或已提交" -ForegroundColor Yellow
}
Write-Host ""

# 2. 提交
Write-Host "[2/6] 提交更改..." -ForegroundColor Yellow
$commitOutput = git commit -m "fix: 添加群組搜索 API (chats.py) 並註冊路由 - 改進搜索邏輯確保 t.me 鏈接始終返回結果" 2>&1
Write-Host $commitOutput
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 提交成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  沒有新更改或提交失敗" -ForegroundColor Yellow
}
Write-Host ""

# 3. 推送
Write-Host "[3/6] 推送到 GitHub..." -ForegroundColor Yellow
$pushOutput = git push origin master 2>&1
Write-Host $pushOutput
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 已推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失敗！" -ForegroundColor Red
    Write-Host "請檢查 GitHub 認證設置" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 4. 顯示最新提交
Write-Host "[4/6] 最新提交:" -ForegroundColor Yellow
git log --oneline -1
Write-Host ""

# 5. 驗證文件
Write-Host "[5/6] 驗證文件已提交..." -ForegroundColor Yellow
$fileCheck = git ls-files api/routers/chats.py
if ($fileCheck) {
    Write-Host "✅ chats.py 已在 Git 中: $fileCheck" -ForegroundColor Green
} else {
    Write-Host "❌ chats.py 未在 Git 中" -ForegroundColor Red
}
Write-Host ""

# 6. 部署到服務器
Write-Host "[6/6] 部署到服務器..." -ForegroundColor Yellow
Write-Host "正在連接服務器..." -ForegroundColor Gray

$serverCmd = @"
cd /opt/luckyred && 
git fetch origin && 
git reset --hard origin/master && 
echo '✅ 代碼已更新' && 
git log --oneline -1 && 
echo '' && 
echo '檢查 chats.py 是否存在...' && 
ls -la api/routers/chats.py && 
echo '' && 
echo '重啟 API 服務...' && 
sudo systemctl restart luckyred-api && 
sleep 2 && 
echo '✅ API 服務已重啟' && 
sudo systemctl status luckyred-api --no-pager | head -12
"@

$serverOutput = ssh ubuntu@165.154.254.99 $serverCmd 2>&1
Write-Host $serverOutput

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 服務器部署成功" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  服務器部署可能失敗" -ForegroundColor Yellow
    Write-Host "請手動執行服務器更新命令" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 完整部署流程完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

