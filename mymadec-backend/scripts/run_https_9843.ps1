# Dev HTTPS for My Madec API on :9843 (self-signed cert in ../certs)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$cert = Join-Path $Root "certs\cert.pem"
$key = Join-Path $Root "certs\key.pem"
if (-not (Test-Path $cert) -or -not (Test-Path $key)) {
  & "$Root\.venv\Scripts\python.exe" "$Root\scripts\generate_dev_ssl.py"
}

# Prefer 9443 if 9843 is stuck/occupied (Windows TIME_WAIT / ghost listeners).
$port = if ($env:MYMADEC_HTTPS_PORT) { [int]$env:MYMADEC_HTTPS_PORT } else { 9443 }

& "$Root\.venv\Scripts\python.exe" -m uvicorn app.main:app `
  --host 0.0.0.0 `
  --port $port `
  --ssl-certfile $cert `
  --ssl-keyfile $key
