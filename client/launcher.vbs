' ==============================================================================
' launcher.vbs - zero-window launcher for client scripts
'
' Usage (IP-guard software distribution, add BOTH files to the package):
'   wscript.exe launcher.vbs deploy.dist.ps1     (deploy/upgrade client)
'   wscript.exe launcher.vbs clean.ps1           (uninstall client)
'
' Why: launching powershell.exe with -WindowStyle Hidden still flashes a
' console window for an instant (window is created then hidden). wscript is
' a GUI-subsystem program with no console at all; it starts the PowerShell
' script with a hidden window (Run ..., 0, True), so nothing is ever visible
' on the user's desktop.
' ==============================================================================
Set args = WScript.Arguments
If args.Count < 1 Then WScript.Quit 1

Set fso = CreateObject("Scripting.FileSystemObject")
ps1 = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), args(0))
If Not fso.FileExists(ps1) Then WScript.Quit 2

Set sh = CreateObject("WScript.Shell")
' 0 = hidden window, True = wait for completion (so IP-guard gets the result)
sh.Run "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File """ & ps1 & """", 0, True
