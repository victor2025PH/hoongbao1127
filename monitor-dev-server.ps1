# 監控開發服務器狀態
Write-Host "正在監控開發服務器..." -ForegroundColor Cyan
Write-Host "服務器地址: http://localhost:3001" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止監控`n" -ForegroundColor Gray

$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "[$attempt/$maxAttempts] 檢查服務器狀態..." -ForegroundColor Yellow
    
    # 檢查端口
    $portCheck = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
    if ($portCheck) {
        Write-Host "[✓] 端口 3001 正在監聽" -ForegroundColor Green
        
        # 嘗試訪問服務器
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            Write-Host "[✓] 服務器響應正常！" -ForegroundColor Green
            Write-Host "[✓] 可以訪問: http://localhost:3001" -ForegroundColor Green
            Write-Host "`n服務器運行正常，監控將繼續..." -ForegroundColor Cyan
            Start-Sleep -Seconds 10
        } catch {
            Write-Host "[等待] 服務器正在啟動中..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    } else {
        Write-Host "[等待] 服務器尚未啟動..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

Write-Host "`n監控完成" -ForegroundColor Cyan

