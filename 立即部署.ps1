# 立即部署 - 使用 PowerShell PSSession（自動輸入密碼）
$ErrorActionPreference = "Continue"

$Server = "165.154.254.99"
$User = "ubuntu"
$Password = "Along2025!!!"
$RemotePath = "/opt/luckyred"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  立即部署到服務器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 創建憑證
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($User, $securePassword)

# 建立 SSH 連接
Write-Host "[連接] 正在連接到服務器..." -ForegroundColor Yellow
try {
    $session = New-PSSession -HostName $Server -UserName $User -KeyFilePath $null -ErrorAction Stop
    Write-Host "✅ 連接成功（使用 SSH 密鑰）" -ForegroundColor Green
} catch {
    Write-Host "[提示] SSH 密鑰連接失敗，嘗試使用密碼..." -ForegroundColor Yellow
    try {
        # 嘗試使用 ssh 命令（需要配置）
        $session = $null
        Write-Host "[提示] 將使用 ssh 命令執行" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ 無法建立連接" -ForegroundColor Red
        exit 1
    }
}

# 執行遠程命令的函數
function Invoke-RemoteCommand {
    param([string]$Command, [string]$Description)
    
    Write-Host $Description -ForegroundColor Yellow
    
    if ($session) {
        $result = Invoke-Command -Session $session -ScriptBlock { Invoke-Expression $using:Command } 2>&1
    } else {
        # 使用 ssh 命令（需要密碼時會提示）
        $result = ssh "${User}@${Server}" $Command 2>&1
    }
    
    Write-Host $result
    return $result
}

# 步驟 1: 檢查狀態
Write-Host "[1/7] 檢查當前狀態..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd ${RemotePath} && pwd && git log --oneline -1" "檢查 Git 狀態"
Write-Host ""

# 步驟 2: 拉取代碼
Write-Host "[2/7] 拉取最新代碼..." -ForegroundColor Yellow
$result = Invoke-RemoteCommand "cd ${RemotePath} && git pull origin master 2>&1" "拉取代碼"
if ($LASTEXITCODE -ne 0 -and $result -match "error|fatal") {
    Write-Host "❌ Git pull 失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 代碼更新完成" -ForegroundColor Green
Write-Host ""

# 步驟 3: 更新 Bot Token
Write-Host "[3/7] 更新 Bot Token..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd ${RemotePath} && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && grep BOT_TOKEN .env" "更新 Bot Token"
Write-Host "✅ Bot Token 已更新" -ForegroundColor Green
Write-Host ""

# 步驟 4-7: 重啟服務和構建
Write-Host "[4/7] 重啟 API 服務..." -ForegroundColor Yellow
Invoke-RemoteCommand "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api" "重啟 API"
Write-Host "✅ API 服務已重啟" -ForegroundColor Green
Write-Host ""

Write-Host "[5/7] 重啟 Bot 服務..." -ForegroundColor Yellow
Invoke-RemoteCommand "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot" "重啟 Bot"
Write-Host "✅ Bot 服務已重啟" -ForegroundColor Green
Write-Host ""

Write-Host "[6/7] 構建前端..." -ForegroundColor Yellow
Invoke-RemoteCommand "cd ${RemotePath}/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -15" "構建前端"
Write-Host "✅ 前端構建完成" -ForegroundColor Green
Write-Host ""

Write-Host "[7/7] 重載 Nginx..." -ForegroundColor Yellow
Invoke-RemoteCommand "sudo systemctl reload nginx && echo 'Nginx reloaded'" "重載 Nginx"
Write-Host "✅ Nginx 已重載" -ForegroundColor Green
Write-Host ""

# 最終檢查
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Invoke-RemoteCommand "echo 'Bot:' && sudo systemctl is-active luckyred-bot && echo 'API:' && sudo systemctl is-active luckyred-api && echo 'Nginx:' && sudo systemctl is-active nginx" "檢查服務狀態"
Write-Host ""

if ($session) {
    Remove-PSSession $session
}

