# Upload CTGS seed data from PC to VPS and run seed-ctgs-vps.sh
# Usage:
#   .\scripts\seed-ctgs-from-pc.ps1 -KeyPath "$env:USERPROFILE\.ssh\my_madec_deploy"

param(
    [Parameter(Mandatory = $true)]
    [string]$KeyPath,
    [string]$Host = "194.164.72.226",
    [string]$User = "root",
    [string]$DataRoot = "d:\Mymadic"
)

$ErrorActionPreference = "Stop"
$ssh = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=30")
$target = "${User}@${Host}"

foreach ($p in @(
    "$DataRoot\ctgs",
    "$DataRoot\my-madic-catalog.csv",
    "$DataRoot\product-images"
)) {
    if (-not (Test-Path $p)) { throw "Missing: $p" }
}

Write-Host "==> Upload seed data to /tmp/seed-data on VPS..."
& ssh @ssh $target "rm -rf /tmp/seed-data && mkdir -p /tmp/seed-data"

& scp @ssh -r "$DataRoot\ctgs" "${target}:/tmp/seed-data/"
& scp @ssh "$DataRoot\my-madic-catalog.csv" "${target}:/tmp/seed-data/"
& scp @ssh -r "$DataRoot\product-images" "${target}:/tmp/seed-data/"

$repoRoot = Split-Path $PSScriptRoot -Parent
& scp @ssh "$repoRoot\scripts\seed-ctgs-vps.sh" "${target}:/root/my-madec/backend/scripts/"

Write-Host "==> Run seed on server..."
& ssh @ssh $target "chmod +x /root/my-madec/backend/scripts/seed-ctgs-vps.sh && /root/my-madec/backend/scripts/seed-ctgs-vps.sh"

Write-Host "Done."
