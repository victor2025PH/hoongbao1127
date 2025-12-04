$Server = "ubuntu@165.154.254.99"
$RemotePath = "/opt/luckyred"
$LocalPath = "C:\hbgm001"

Write-Host "========================================"
Write-Host "  Security Layer Deploy"
Write-Host "========================================"

$files = @(
    "api/middleware/__init__.py",
    "api/middleware/anti_sybil.py",
    "api/services/__init__.py",
    "api/services/liquidity_service.py",
    "api/routers/v2/__init__.py",
    "api/routers/v2/auth.py",
    "api/routers/v2/security.py",
    "api/main.py",
    "shared/database/models.py",
    "bot/handlers/__init__.py",
    "bot/handlers/web_login.py",
    "frontend/src/utils/platformRules.ts",
    "frontend/src/utils/fingerprint.ts",
    "frontend/src/components/ComplianceBanner.tsx",
    "migrations/安全與合規層遷移.sql",
    "deploy-security-on-server.sh"
)

Write-Host "[1/3] Creating remote directories..."
$cmd = "mkdir -p /opt/luckyred/api/middleware /opt/luckyred/api/services /opt/luckyred/api/routers/v2 /opt/luckyred/frontend/src/utils /opt/luckyred/frontend/src/components /opt/luckyred/migrations"
ssh $Server $cmd

Write-Host "[2/3] Uploading files..."
foreach ($file in $files) {
    $local = Join-Path $LocalPath $file
    $remote = "$RemotePath/$file"
    if (Test-Path $local) {
        Write-Host "  Upload: $file"
        scp $local "${Server}:${remote}"
    }
}

Write-Host "[3/3] Setting permissions..."
ssh $Server "chmod -R 755 /opt/luckyred/api /opt/luckyred/bot /opt/luckyred/frontend 2>/dev/null; chmod +x /opt/luckyred/deploy-security-on-server.sh 2>/dev/null"

Write-Host ""
Write-Host "========================================"
Write-Host "  Upload Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Next: SSH to server and run:"
Write-Host "  cd /opt/luckyred"
Write-Host "  ./deploy-security-on-server.sh"
