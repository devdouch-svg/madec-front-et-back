# Create a Python 3.12 venv and install requirements.
# Default `python` on this machine may be 3.14, which cannot install this stack.
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyLauncher) {
    throw "Python launcher 'py' not found. Install Python 3.12 from https://www.python.org/downloads/"
}

$py312 = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
if (-not $py312) {
    throw "Python 3.12 is required (you currently have 3.14 as default). Install 3.12, then re-run this script."
}

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
$recreate = $true
if (Test-Path $venvPython) {
    $ver = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($ver -eq "3.12") { $recreate = $false }
}

if ($recreate) {
    Write-Host "Creating Python 3.12 virtualenv in .venv ..."
    if (Test-Path (Join-Path $Root ".venv")) {
        Remove-Item -Recurse -Force (Join-Path $Root ".venv")
    }
    & py -3.12 -m venv .venv
}

Write-Host "Installing requirements with $( & $venvPython --version ) ..."
& $venvPython -m pip install -U pip
& $venvPython -m pip install -r (Join-Path $Root "requirements.txt")
Write-Host ""
Write-Host "Install OK. Next:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  uvicorn app.main:app --reload"
