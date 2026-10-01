param([switch]$Team, [switch]$Monitoring, [switch]$Grafana, [switch]$Observability, [switch]$Alerts)
if ($Alerts) { $Observability = $true }
if ($Observability) { $Team = $true; $Monitoring = $true }
$ErrorActionPreference = 'Stop'
$dockerExecutable = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $dockerExecutable) {
    $perUserDocker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
    if (Test-Path -LiteralPath $perUserDocker) { $dockerExecutable = $perUserDocker }
}
if (-not $dockerExecutable) {
    throw 'Docker is not installed/on PATH. Install Docker Desktop with Linux containers, then rerun. No stack started.'
}
& $dockerExecutable info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker engine is not ready. Start Docker Desktop first.' }
$infraRoot = Split-Path -Parent $PSScriptRoot
$composeArgs = @('compose', '--project-directory', $infraRoot, '-f', (Join-Path $infraRoot 'compose.yaml'))
if ($Team) { $composeArgs += @('-f', (Join-Path $infraRoot 'compose.team.yaml')) }
if ($Monitoring -or $Grafana) { $composeArgs += @('-f', (Join-Path $infraRoot 'compose.monitoring.yaml')) }
if ($Grafana) { $composeArgs += @('-f', (Join-Path $infraRoot 'compose.grafana.yaml')) }
if ($Observability) { $composeArgs += @('-f', (Join-Path $infraRoot 'compose.observability.yaml')) }
if ($Alerts) { $composeArgs += @('-f', (Join-Path $infraRoot 'compose.alerts.yaml')) }
& $dockerExecutable @composeArgs config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Compose configuration failed. Check credentials and required environment variables.' }
& $dockerExecutable @composeArgs up --build -d --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Startup/build failed; inspect docker compose logs. Existing volumes were preserved.' }
& $dockerExecutable @composeArgs ps
