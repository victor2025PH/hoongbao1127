# 本地開發環境啟動腳本

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LuckyRed 本地開發環境啟動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 .env 文件
Write-Host "[1/5] 檢查環境配置..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env 文件不存在，從 .env.example 創建..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ 已創建 .env 文件，請編輯填入實際值" -ForegroundColor Green
        Write-Host "  重要：請編輯 .env 文件填入 BOT_TOKEN 和 DATABASE_URL" -ForegroundColor Red
    } else {
        Write-Host "✗ .env.example 文件不存在" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ .env 文件存在" -ForegroundColor Green
}

# 檢查 Python 虛擬環境
Write-Host ""
Write-Host "[2/5] 檢查 Python 環境..." -ForegroundColor Yellow
if (-not (Test-Path "api\.venv")) {
    Write-Host "創建 API 虛擬環境..." -ForegroundColor Yellow
    python -m venv api\.venv
    Write-Host "✓ 虛擬環境已創建" -ForegroundColor Green
}

# 激活虛擬環境並安裝依賴
Write-Host "安裝 API 依賴..." -ForegroundColor Yellow
& "api\.venv\Scripts\Activate.ps1"
pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "✓ API 依賴已安裝" -ForegroundColor Green
deactivate

# 檢查 Node.js 依賴
Write-Host ""
Write-Host "[3/5] 檢查前端依賴..." -ForegroundColor Yellow
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "安裝前端依賴..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✓ 前端依賴已安裝" -ForegroundColor Green
} else {
    Write-Host "✓ 前端依賴已存在" -ForegroundColor Green
}

# 啟動 API 服務器
Write-Host ""
Write-Host "[4/5] 啟動 API 服務器..." -ForegroundColor Yellow
Write-Host "API 將在 http://localhost:8080 運行" -ForegroundColor Cyan

$apiProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\api'; .\.venv\Scripts\Activate.ps1; python main.py" -PassThru
Start-Sleep -Seconds 2

if ($apiProcess.HasExited) {
    Write-Host "✗ API 服務器啟動失敗" -ForegroundColor Red
} else {
    Write-Host "✓ API 服務器已啟動 (PID: $($apiProcess.Id))" -ForegroundColor Green
}

# 啟動前端開發服務器
Write-Host ""
Write-Host "[5/5] 啟動前端開發服務器..." -ForegroundColor Yellow
Write-Host "前端將在 http://localhost:3001 運行" -ForegroundColor Cyan

$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev" -PassThru
Start-Sleep -Seconds 2

if ($frontendProcess.HasExited) {
    Write-Host "✗ 前端服務器啟動失敗" -ForegroundColor Red
} else {
    Write-Host "✓ 前端服務器已啟動 (PID: $($frontendProcess.Id))" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  本地開發環境已啟動！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "服務地址：" -ForegroundColor Cyan
Write-Host "  🌐 前端: http://localhost:3001" -ForegroundColor Yellow
Write-Host "  🔧 API:  http://localhost:8080" -ForegroundColor Yellow
Write-Host "  📚 API 文檔: http://localhost:8080/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "測試步驟：" -ForegroundColor Cyan
Write-Host "  1. 訪問 http://localhost:3001" -ForegroundColor White
Write-Host "  2. 進入 Wallet 頁面" -ForegroundColor White
Write-Host "  3. 點擊「發紅包」按鈕" -ForegroundColor White
Write-Host "  4. 檢查遊戲規則彈窗是否自動顯示" -ForegroundColor White
Write-Host "  5. 檢查「✨ 遊戲規則 ✨」按鈕" -ForegroundColor White
Write-Host ""
Write-Host "停止服務：" -ForegroundColor Cyan
Write-Host "  關閉打開的 PowerShell 窗口即可停止服務" -ForegroundColor White
Write-Host ""
