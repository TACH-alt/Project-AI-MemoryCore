param(
    [int]$Port = 8765
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

& $Python.Source $Frontend --project-root $ProjectRoot --port $Port
