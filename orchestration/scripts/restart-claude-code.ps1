# Restart Claude Code CLI - nightly maintenance
# Created for Legend by Clover (MemoryCore) on 2026-06-04
#
# Behavior:
#   1. Stops ONLY the Claude Code CLI process (npm global install).
#      The Claude Desktop app (WindowsApps\Claude_*) is deliberately left alone.
#   2. Relaunches a fresh Claude Code window via Windows Terminal (falls back to cmd).
#
# Intended to run from Task Scheduler task "Restart Claude Code Daily" at 00:00.

$ErrorActionPreference = 'SilentlyContinue'

# Path signature that uniquely identifies the Claude Code CLI (NOT the desktop app)
$cliPathPattern = '*\npm\node_modules\@anthropic-ai\claude-code\*'
$launchDir      = 'C:\Users\Legend\Documents\Claude\Projects\MemoryCore'
$logFile        = 'C:\Users\Legend\Documents\Claude\Projects\MemoryCore\orchestration\logs\restart-claude-code.log'

# Ensure log directory exists
$logDir = Split-Path $logFile
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log($msg) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $logFile -Value "[$ts] $msg"
}

Write-Log '=== Nightly Claude Code restart triggered ==='

# 0. Continuity safety net: checkpoint/commit the session BEFORE killing anything,
#    so the next session can continue from the last one.
$checkpoint = Join-Path (Split-Path $PSCommandPath) 'checkpoint-session.ps1'
if (Test-Path $checkpoint) {
    Write-Log 'Running pre-restart checkpoint...'
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $checkpoint
        Write-Log 'Pre-restart checkpoint completed.'
    } catch {
        Write-Log "Checkpoint step error (continuing with restart): $($_.Exception.Message)"
    }
} else {
    Write-Log "WARNING: checkpoint-session.ps1 not found at $checkpoint"
}

# 1. Stop only the Claude Code CLI (leave Claude Desktop app running)
$cliProcs = Get-Process -Name claude -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -like $cliPathPattern }

if ($cliProcs) {
    foreach ($p in $cliProcs) {
        Write-Log "Stopping Claude Code CLI PID $($p.Id) - $($p.Path)"
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Log 'No Claude Code CLI process found running.'
}

Start-Sleep -Seconds 2

# 2. Relaunch a fresh Claude Code window
$wt = (Get-Command wt.exe -ErrorAction SilentlyContinue).Source
try {
    if ($wt) {
        # Open Windows Terminal in the MemoryCore dir, running claude via cmd (/k keeps window open)
        Start-Process $wt -ArgumentList @('-d', $launchDir, 'cmd', '/k', 'claude')
        Write-Log "Relaunched Claude Code in Windows Terminal at $launchDir"
    } else {
        Start-Process 'cmd.exe' -ArgumentList @('/k', 'claude') -WorkingDirectory $launchDir
        Write-Log "Windows Terminal not found; relaunched Claude Code in cmd at $launchDir"
    }
} catch {
    Write-Log "Relaunch FAILED: $($_.Exception.Message)"
}

Write-Log '=== Done ==='
