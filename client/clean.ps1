# ==============================================================================
# clean.ps1 v1 - uninstall IP tracker client (silent, no console window)
# Run via IP-guard software distribution as SYSTEM, same mechanism as deploy.ps1:
#   powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File clean.ps1
# Replaces clean_all_fixed.bat: bat files may flash a console window on user
# desktops; PowerShell launched with -WindowStyle Hidden is fully invisible.
# Steps: stop task -> kill processes locking files -> delete task -> delete
# install dir (3 retries) -> delete logs -> write per-step result to log file.
# ==============================================================================

$LOG = "$env:TEMP\ip_uninstall.log"
function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try { [System.IO.File]::AppendAllText($LOG, "$ts $msg`r`n", [System.Text.Encoding]::UTF8) } catch {}
}

Log "=== clean.ps1 start ==="

# 1. stop scheduled task instances (twice, small gap to dodge a run just starting)
schtasks /End /TN "Company_IP_Tracker" /F 2>$null | Out-Null
Start-Sleep -Seconds 2
schtasks /End /TN "Company_IP_Tracker" /F 2>$null | Out-Null

# 2. kill any powershell running the report script (match by install path in
#    command line; exclude self so we do not kill ourselves)
function Kill-ReportProcs {
    Get-CimInstance Win32_Process | Where-Object {
        $_.ProcessId -ne $PID -and $_.Name -eq 'powershell.exe' -and
        $_.CommandLine -like '*Company_Network*'
    } | ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
}
Kill-ReportProcs
Start-Sleep -Seconds 1

# 3. delete scheduled task (incl. legacy name from very old versions)
schtasks /Delete /TN "Company_IP_Tracker" /F 2>$null | Out-Null
schtasks /Delete /TN "IPTrackerReport" /F 2>$null | Out-Null

# 4. delete install directory with retries
for ($i = 1; $i -le 3; $i++) {
    if (-not (Test-Path "C:\ProgramData\Company_Network")) { break }
    Kill-ReportProcs
    Start-Sleep -Seconds 2
    Remove-Item "C:\ProgramData\Company_Network" -Recurse -Force -ErrorAction SilentlyContinue
}

# 5. delete logs
Remove-Item "$env:TEMP\ip_report.log", "$env:TEMP\deploy_debug.log", "$env:TEMP\uninstall_debug.log" -Force -ErrorAction SilentlyContinue

# 6. result summary -> log
$taskGone = -not (schtasks /query /TN "Company_IP_Tracker" 2>$null)
$dirGone  = -not (Test-Path "C:\ProgramData\Company_Network")
$logGone  = -not (Test-Path "$env:TEMP\ip_report.log")
Log ("RESULT task_deleted={0} dir_deleted={1} logs_deleted={2}" -f $taskGone, $dirGone, $logGone)
if (-not $dirGone) { Log "NOTE: directory remains, reboot then run clean.ps1 again" }
Log "=== clean.ps1 done ==="
