# Local equivalent of Member 4 test jobs. Does not activate GitHub or deploy.
param([switch]$Runtime)
$ErrorActionPreference = 'Stop'
$infraRoot = Split-Path -Parent $PSScriptRoot
$optimizerPython = Join-Path $infraRoot '.venv\Scripts\python.exe'
$federationPython = Join-Path $infraRoot '.venv-federated\Scripts\python.exe'
foreach ($pythonPath in @($optimizerPython, $federationPython)) {
    if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Required environment missing: $pythonPath" }
}
Push-Location $infraRoot
try {
    & $optimizerPython -m unittest discover -s optimization/tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Optimization checks failed' }
    & $federationPython -m unittest discover -s federated/tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Federation checks failed' }
    & $federationPython -m unittest discover -s monitoring/tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Monitoring/recovery checks failed' }
    if ($Runtime) {
        & $federationPython deployment/verify_local.py --observability --grafana
        if ($LASTEXITCODE -ne 0) { throw 'Runtime acceptance failed' }
        & $federationPython deployment/verify_local_alerts.py
        if ($LASTEXITCODE -ne 0) { throw 'Local alert delivery failed' }
    }
    Write-Output 'Member 4 local checks passed. Security scans and hosted CI are separate gates.'
}
finally { Pop-Location }
