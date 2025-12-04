# 部署管理後台安全中心模組
# 使用方式: .\deploy-admin-security.ps1

$SERVER = "ubuntu@165.154.254.99"
$REMOTE_PATH = "/opt/luckyred"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署管理後台安全中心模組" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 後端文件
$backendFiles = @(
    "api/routers/admin_security.py",
    "api/main.py"
)

# 前端文件
$frontendFiles = @(
    "admin/frontend/src/App.tsx",
    "admin/frontend/src/utils/api.ts",
    "admin/frontend/src/components/Layout/index.tsx",
    "admin/frontend/src/pages/Dashboard.tsx",
    "admin/frontend/src/pages/SecurityDashboard.tsx",
    "admin/frontend/src/pages/RiskMonitor.tsx",
    "admin/frontend/src/pages/DeviceManagement.tsx",
    "admin/frontend/src/pages/IPMonitor.tsx",
    "admin/frontend/src/pages/AlertLogs.tsx",
    "admin/frontend/src/pages/LiquidityManagement.tsx"
)

Write-Host ""
Write-Host "[1/4] 上傳後端文件..." -ForegroundColor Yellow

foreach ($file in $backendFiles) {
    Write-Host "  上傳: $file"
    scp $file "${SERVER}:${REMOTE_PATH}/$file"
}

Write-Host ""
Write-Host "[2/4] 上傳前端文件..." -ForegroundColor Yellow

foreach ($file in $frontendFiles) {
    Write-Host "  上傳: $file"
    scp $file "${SERVER}:${REMOTE_PATH}/$file"
}

Write-Host ""
Write-Host "[3/4] 在服務器上重啟 API..." -ForegroundColor Yellow
ssh $SERVER "sudo systemctl restart luckyred-api"

Write-Host ""
Write-Host "[4/4] 重新構建管理後台前端..." -ForegroundColor Yellow
ssh $SERVER "cd ${REMOTE_PATH}/admin/frontend && npm install && npm run build"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "請訪問管理後台查看新的安全中心功能:" -ForegroundColor Cyan
Write-Host "  https://admin.usdt2026.cc/security" -ForegroundColor White
Write-Host ""
