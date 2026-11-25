# Deploy My Madec backend to VPS from Windows (manual — when GitHub Actions SSH fails).
# Usage:
#   .\scripts\deploy-vps.ps1 -KeyPath "$env:USERPROFILE\.ssh\my_madec_deploy"
#   .\scripts\deploy-vps.ps1 -KeyPath "C:\path\to\deploy_key" -Host 194.164.72.226 -User root

param(
    [Parameter(Mandatory = $true)]
    [string]$KeyPath,
    [string]$Host = "194.164.72.226",
    [string]$User = "root",
    [string]$RemoteDir = "/root/my-madec/backend",
    [switch]$SkipCatalogReset = $true
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $KeyPath)) {
    Write-Error "SSH key not found: $KeyPath`nCopy VPS_SSH_KEY from GitHub Secrets to this file first."
}

$ssh = @(
    "-i", $KeyPath,
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=30"
)
$target = "${User}@${Host}"

$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
Write-Host "==> Repo: $repoRoot"

Write-Host "==> Test SSH..."
& ssh @ssh $target "echo SSH_OK"
if ($LASTEXITCODE -ne 0) { throw "SSH failed" }

Write-Host "==> Prepare remote dir..."
& ssh @ssh $target "mkdir -p $RemoteDir"

Write-Host "==> Upload code (exclude .git, .env)..."
$archive = Join-Path $env:TEMP "my-madec-backend.tgz"
if (Test-Path $archive) { Remove-Item $archive -Force }
& tar --exclude=.git --exclude=__pycache__ --exclude=*.pyc --exclude=.env -czf $archive .
& scp @ssh $archive "${target}:${RemoteDir}/backend.tgz"
Remove-Item $archive -Force
& ssh @ssh $target "cd $RemoteDir && tar -xzf backend.tgz && rm -f backend.tgz"

if ($SkipCatalogReset) {
    Write-Host "==> Protect CTGS data: RESET_MADEC_CATALOG=false in .env"
    & ssh @ssh $target @"
if [ -f $RemoteDir/.env ]; then
  if grep -q '^RESET_MADEC_CATALOG=' $RemoteDir/.env; then
    sed -i 's/^RESET_MADEC_CATALOG=.*/RESET_MADEC_CATALOG=false/' $RemoteDir/.env
  else
    echo 'RESET_MADEC_CATALOG=false' >> $RemoteDir/.env
  fi
else
  echo 'WARNING: no .env on server — create one before API can start'
fi
"@
}

Write-Host "==> Docker build + start..."
& ssh @ssh $target @"
set -e
cd $RemoteDir
docker network create madec-net 2>/dev/null || true
docker network connect madec-net my-madec-mssql-mssql-1 2>/dev/null || true
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
echo 'Waiting for API...'
for i in \$(seq 1 30); do
  if docker compose -f docker-compose.prod.yml exec -T api curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo 'API healthy'
    exit 0
  fi
  sleep 5
done
echo 'API not healthy yet — logs:'
docker logs --tail 40 backend-api-1 2>&1 || true
exit 1
"@

Write-Host "==> Health check from PC..."
Start-Sleep -Seconds 3
try {
    $r = Invoke-WebRequest -Uri "http://${Host}:8000/health" -TimeoutSec 15 -UseBasicParsing
    Write-Host "HTTP $($r.StatusCode) — $($r.Content)"
} catch {
    Write-Warning "External health check failed: $_"
    Write-Host "Check: ssh ... 'docker logs backend-api-1 --tail 50'"
}

Write-Host "Done."
