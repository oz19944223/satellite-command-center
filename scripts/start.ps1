$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Not installed yet. Run .\scripts\install.ps1 first." }
$env:PYTHONPATH = Join-Path $Root "backend"
Write-Host "Satellite Command Center: http://127.0.0.1:8000" -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000"
& $Python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
