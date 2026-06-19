param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

Write-Host "[1/3] Creating virtual environment"
& $Python -m venv .venv

Write-Host "[2/3] Installing dependencies"
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[3/3] Starting Azure Functions host"
func start
