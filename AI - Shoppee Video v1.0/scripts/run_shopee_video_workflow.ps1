param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Masterlist = Join-Path $ProjectRoot "masterlist\List of Link Shopee VIdeo.csv"
$Processor = Join-Path $ProjectRoot "scripts\process_shopee_video.py"

if (-not (Test-Path -LiteralPath $Masterlist)) {
    throw "Masterlist not found: $Masterlist"
}

if (-not (Test-Path -LiteralPath $Processor)) {
    throw "Processor not found: $Processor"
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python was not found on PATH."
}

$ArgsList = @(
    $Processor,
    "--project-root",
    $ProjectRoot,
    "--masterlist",
    $Masterlist
)

if ($DryRun) {
    $ArgsList += "--dry-run"
}

if ($Force) {
    $ArgsList += "--force"
}

Write-Host "AI - Shoppee Video v1.0 workflow"
Write-Host "Project root: $ProjectRoot"
Write-Host "Masterlist: $Masterlist"

& $Python.Source @ArgsList
exit $LASTEXITCODE
