param(
    [int]$Port = 8765,
    [switch]$Lan
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Frontend = Join-Path $ProjectRoot "scripts\shoppee_video_frontend.py"

if (-not (Test-Path -LiteralPath $Frontend)) {
    throw "Frontend script not found: $Frontend"
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python was not found on PATH."
}

$ArgsList = @(
    $Frontend,
    "--project-root",
    $ProjectRoot,
    "--port",
    $Port
)

if ($Lan) {
    $ArgsList += @("--host", "0.0.0.0")
}

& $Python.Source @ArgsList
