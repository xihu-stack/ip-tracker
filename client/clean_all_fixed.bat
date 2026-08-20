@echo off
:: ==============================================================================
:: clean_all_fixed.bat v2 - uninstall IP tracker client
:: Run via IP-guard software distribution as SYSTEM (silent).
:: v2: kill processes locking the files before deleting, retry dir delete,
::     print per-step result at the end. ASCII-only to avoid codepage issues.
:: ==============================================================================

echo [1/4] Stop task instances...
schtasks /End /TN "Company_IP_Tracker" /F >nul 2>&1
ping 127.0.0.1 -n 3 >nul 2>&1
schtasks /End /TN "Company_IP_Tracker" /F >nul 2>&1

echo [2/4] Kill running report processes (identified by install path in command line)...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -eq 'powershell.exe' -and $_.CommandLine -like '*Company_Network*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
ping 127.0.0.1 -n 2 >nul 2>&1

echo [3/4] Delete scheduled task...
schtasks /Delete /TN "Company_IP_Tracker" /F >nul 2>&1

echo [4/4] Delete install directory with retry...
rd /s /q "C:\ProgramData\Company_Network" >nul 2>&1
if exist "C:\ProgramData\Company_Network" (
    powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -eq 'powershell.exe' -and $_.CommandLine -like '*Company_Network*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
    ping 127.0.0.1 -n 3 >nul 2>&1
    rd /s /q "C:\ProgramData\Company_Network" >nul 2>&1
)
if exist "C:\ProgramData\Company_Network" (
    ping 127.0.0.1 -n 4 >nul 2>&1
    rd /s /q "C:\ProgramData\Company_Network" >nul 2>&1
)

del /f /q "%TEMP%\ip_report.log" >nul 2>&1
del /f /q "%TEMP%\deploy_debug.log" >nul 2>&1
del /f /q "%TEMP%\uninstall_debug.log" >nul 2>&1

echo.
echo ============ RESULT ============
schtasks /query /TN "Company_IP_Tracker" >nul 2>&1
if %errorlevel%==0 (echo [X] Task STILL EXISTS) else (echo [OK] Task deleted)
if exist "C:\ProgramData\Company_Network" (echo [X] Directory STILL EXISTS - reboot and run again) else (echo [OK] Directory deleted)
if exist "%TEMP%\ip_report.log" (echo [X] Log still exists) else (echo [OK] Logs deleted)
echo ================================
exit /b 0
