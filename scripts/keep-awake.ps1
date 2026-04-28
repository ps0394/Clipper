<#
.SYNOPSIS
    Keeps the machine awake (no sleep, no display off) for the duration this script runs.

.DESCRIPTION
    Uses the Win32 SetThreadExecutionState API with ES_CONTINUOUS | ES_SYSTEM_REQUIRED |
    ES_DISPLAY_REQUIRED to inhibit sleep and display blanking. The keep-awake state lasts
    only while this script's process is running. Closing the window or pressing Ctrl+C
    immediately restores normal power behavior.

    No registry changes, no admin rights required, no policy overrides.

.PARAMETER KeepDisplayOn
    If set, also prevent the display from turning off. Default: $false (display can sleep,
    system stays awake). For long unattended runs, leaving display sleep enabled saves power.

.EXAMPLE
    .\scripts\keep-awake.ps1
    Keep system awake; allow display sleep. Run in a terminal window and leave open.

.EXAMPLE
    .\scripts\keep-awake.ps1 -KeepDisplayOn
    Keep both system AND display awake.
#>
[CmdletBinding()]
param(
    [switch]$KeepDisplayOn
)

$ErrorActionPreference = "Stop"

# Win32 flags
$ES_CONTINUOUS       = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED  = [uint32]"0x00000001"
$ES_DISPLAY_REQUIRED = [uint32]"0x00000002"

# P/Invoke
if (-not ("PInvoke.PowerMgmt" -as [type])) {
    Add-Type -Namespace PInvoke -Name PowerMgmt -MemberDefinition @"
[System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
"@
}

$flags = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED
if ($KeepDisplayOn) { $flags = $flags -bor $ES_DISPLAY_REQUIRED }

$prev = [PInvoke.PowerMgmt]::SetThreadExecutionState($flags)
if ($prev -eq 0) {
    Write-Error "SetThreadExecutionState failed."
    exit 1
}

$mode = if ($KeepDisplayOn) { "system + display" } else { "system only (display can sleep)" }
Write-Host ""
Write-Host "  Keep-awake active: $mode" -ForegroundColor Green
Write-Host "  PID: $PID"
Write-Host "  Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "  Leave this window OPEN for the duration of your long-running task."
Write-Host "  Close the window or press Ctrl+C to release the lock."
Write-Host ""

# Cleanup on exit (Ctrl+C, window close, or normal exit)
$cleanup = {
    [void][PInvoke.PowerMgmt]::SetThreadExecutionState($ES_CONTINUOUS)
    Write-Host ""
    Write-Host "  Keep-awake released at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')." -ForegroundColor Yellow
}
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup | Out-Null

# Heartbeat loop. The actual keep-awake is the SetThreadExecutionState call above —
# this loop just keeps the script alive so the process doesn't terminate.
try {
    $tick = 0
    while ($true) {
        Start-Sleep -Seconds 60
        $tick++
        if ($tick % 30 -eq 0) {
            # Status line every 30 minutes
            Write-Host "  [heartbeat] still awake, $($tick) minute(s) elapsed at $(Get-Date -Format 'HH:mm:ss')"
        }
    }
}
finally {
    & $cleanup
}
