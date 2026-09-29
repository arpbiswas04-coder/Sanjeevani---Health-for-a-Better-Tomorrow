# PowerShell setup script for Sanjeevani Grid
Write-Host "=== Setting up Sanjeevani Grid Development Environment ===" -ForegroundColor Cyan

if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
} else {
    Write-Host ".env already exists, skipping copy." -ForegroundColor Yellow
}

Write-Host "Verifying environment prerequisites..." -ForegroundColor Cyan

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "✓ Node.js found: $(node -v)" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found in PATH" -ForegroundColor Red
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ Python found: $(python --version)" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found in PATH" -ForegroundColor Red
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✓ Docker found: $(docker --version)" -ForegroundColor Green
} else {
    Write-Host "! Docker not found in PATH (Install Docker Desktop if using containers)" -ForegroundColor Yellow
}

Write-Host "`nSetup complete! You can start the stack via:" -ForegroundColor Cyan
Write-Host "  docker compose up --build" -ForegroundColor White
