# Pre-restart session checkpoint - continuity safety net
# Created for Legend by Clover (MemoryCore) on 2026-06-04
#
# Purpose: guarantee that whatever exists on disk at restart time is preserved,
# so the NEXT session can continue from the LAST session.
#
# This is a MECHANICAL backstop. It does NOT replace Clover authoring a rich
# session log / diary / Obsidian note during the session (standing rule).
# It ensures: (a) MemoryCore git commit of any pending work,
#             (b) a timestamped breadcrumb in the Legendary vault,
#             (c) a shared-activity-log line.
#
# Exit code 0 always (never block the restart).

$ErrorActionPreference = 'SilentlyContinue'

$repo     = 'C:\Users\Legend\Documents\Claude\Projects\MemoryCore'
$vault    = 'C:\Users\Legend\Desktop\Obsidian\Legendary'
$sharedLog= Join-Path $repo 'SHARED-ACTIVITY-LOG.md'
$logFile  = Join-Path $repo 'orchestration\logs\checkpoint-session.log'
$ts       = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$dateOnly = Get-Date -Format 'yyyy-MM-dd'

$logDir = Split-Path $logFile
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log($msg) { Add-Content -Path $logFile -Value "[$ts] $msg" }

Write-Log '=== Pre-restart checkpoint started ==='

# 1. Commit any pending MemoryCore work (backstop so nothing is lost)
try {
    Push-Location $repo
    $dirty = git status --porcelain
    if ($dirty) {
        git add -A 2>$null
        git commit -m "chore: nightly auto-checkpoint before restart ($ts)" 2>$null | Out-Null
        Write-Log 'MemoryCore had uncommitted changes -> committed auto-checkpoint.'
    } else {
        Write-Log 'MemoryCore clean - nothing to commit.'
    }
    Pop-Location
} catch {
    Write-Log "MemoryCore commit step error: $($_.Exception.Message)"
    Pop-Location
}

# 2. Drop a timestamped breadcrumb into the Legendary vault (not a git repo)
#    Guarantees a dated vault-side record exists at every restart.
try {
    if (Test-Path $vault) {
        $sysDir = Join-Path $vault '00-System'
        if (-not (Test-Path $sysDir)) { New-Item -ItemType Directory -Path $sysDir -Force | Out-Null }
        $crumbFile = Join-Path $sysDir 'auto-checkpoint-log.md'
        if (-not (Test-Path $crumbFile)) {
            Set-Content -Path $crumbFile -Encoding utf8 -Value "# Auto-Checkpoint Log`r`n*Mechanical breadcrumbs written by checkpoint-session.ps1 before each nightly Claude Code restart. For full session state see MemoryCore/main/current-session.md and the latest 01-Sessions note.*`r`n"
        }
        Add-Content -Path $crumbFile -Encoding utf8 -Value "- [$ts] Nightly restart checkpoint. MemoryCore committed (if dirty). Continuity state in current-session.md."
        Write-Log "Vault breadcrumb appended to $crumbFile"
    } else {
        Write-Log 'Legendary vault not found - skipped breadcrumb.'
    }
} catch {
    Write-Log "Vault breadcrumb step error: $($_.Exception.Message)"
}

# 3. Shared activity log line (read on next 'Legend' trigger)
try {
    if (Test-Path $sharedLog) {
        Add-Content -Path $sharedLog -Encoding utf8 -Value "[$ts] [TOOL: claude] Nightly auto-checkpoint before scheduled restart."
        Write-Log 'SHARED-ACTIVITY-LOG line appended.'
    }
} catch {
    Write-Log "Shared log step error: $($_.Exception.Message)"
}

Write-Log '=== Pre-restart checkpoint done ==='
exit 0
