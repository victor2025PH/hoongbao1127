# 全自動部署腳本 - 支持密碼自動輸入
$ErrorActionPreference = "Continue"

$Server = "165.154.254.99"
$User = "ubuntu"
$Password = "Along2025!!!"
$RemotePath = "/opt/luckyred"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  全自動部署（自動輸入密碼）" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查是否安裝了 sshpass
$hasSshpass = $false
if (Get-Command sshpass -ErrorAction SilentlyContinue) {
    $hasSshpass = $true
    Write-Host "[OK] 檢測到 sshpass 工具" -ForegroundColor Green
} else {
    Write-Host "[提示] 未檢測到 sshpass，將使用其他方法" -ForegroundColor Yellow
}

# 執行 SSH 命令的函數
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host $Description -ForegroundColor Yellow
    
    if ($hasSshpass) {
        # 使用 sshpass
        $env:SSHPASS = $Password
        $result = sshpass -e ssh -o StrictHostKeyChecking=no "${User}@${Server}" $Command 2>&1
        Write-Host $result
        return $LASTEXITCODE -eq 0
    } else {
        # 使用 plink（如果可用）
        if (Get-Command plink -ErrorAction SilentlyContinue) {
            $result = echo $Password | plink -ssh -pw $Password "${User}@${Server}" $Command 2>&1
            Write-Host $result
            return $LASTEXITCODE -eq 0
        } else {
            # 使用 PowerShell PSSession
            try {
                $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
                $credential = New-Object System.Management.Automation.PSCredential($User, $securePassword)
                $session = New-PSSession -ComputerName $Server -Credential $credential -ErrorAction Stop
                $result = Invoke-Command -Session $session -ScriptBlock { Invoke-Expression $using:Command } 2>&1
                Write-Host $result
                Remove-PSSession $session
                return $true
            } catch {
                Write-Host "❌ 無法建立 SSH 連接: $_" -ForegroundColor Red
                Write-Host "請安裝 sshpass 或 plink" -ForegroundColor Yellow
                return $false
            }
        }
    }
}

# 步驟 1: 檢查當前狀態
Write-Host "[1/7] 檢查當前狀態..." -ForegroundColor Yellow
Invoke-SSHCommand "cd ${RemotePath} && pwd && git log --oneline -1 && git status --short" "檢查 Git 狀態"
Write-Host ""

# 步驟 2: 拉取代碼
Write-Host "[2/7] 拉取最新代碼..." -ForegroundColor Yellow
$success = Invoke-SSHCommand "cd ${RemotePath} && git pull origin master 2>&1" "拉取代碼"
if (-not $success) {
    Write-Host "❌ Git pull 失敗" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 代碼更新完成" -ForegroundColor Green
Write-Host ""

# 步驟 3: 更新 Bot Token
Write-Host "[3/7] 更新 Bot Token..." -ForegroundColor Yellow
Invoke-SSHCommand "cd ${RemotePath} && sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=8271541107:AAH1YPO82cRzcwcdY9GEloejvNmpKiAxTrs/' .env && grep BOT_TOKEN .env" "更新 Bot Token"
Write-Host "✅ Bot Token 已更新" -ForegroundColor Green
Write-Host ""

# 步驟 4: 重啟 API
Write-Host "[4/7] 重啟 API 服務..." -ForegroundColor Yellow
Invoke-SSHCommand "sudo systemctl restart luckyred-api && sleep 2 && sudo systemctl is-active luckyred-api" "重啟 API"
Write-Host "✅ API 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 5: 重啟 Bot
Write-Host "[5/7] 重啟 Bot 服務..." -ForegroundColor Yellow
Invoke-SSHCommand "sudo systemctl restart luckyred-bot && sleep 2 && sudo systemctl is-active luckyred-bot" "重啟 Bot"
Write-Host "✅ Bot 服務已重啟" -ForegroundColor Green
Write-Host ""

# 步驟 6: 構建前端
Write-Host "[6/7] 構建前端（這可能需要幾分鐘）..." -ForegroundColor Yellow
Invoke-SSHCommand "cd ${RemotePath}/frontend && sudo rm -rf dist && npm run build 2>&1 | tail -15" "構建前端"
Write-Host "✅ 前端構建完成" -ForegroundColor Green
Write-Host ""

# 步驟 7: 重載 Nginx
Write-Host "[7/7] 重載 Nginx..." -ForegroundColor Yellow
Invoke-SSHCommand "sudo systemctl reload nginx && echo 'Nginx reloaded'" "重載 Nginx"
Write-Host "✅ Nginx 已重載" -ForegroundColor Green
Write-Host ""

# 最終檢查
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  部署完成！服務狀態：" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Invoke-SSHCommand "echo 'Bot:' && sudo systemctl is-active luckyred-bot && echo 'API:' && sudo systemctl is-active luckyred-api && echo 'Nginx:' && sudo systemctl is-active nginx" "檢查服務狀態"
Write-Host ""

