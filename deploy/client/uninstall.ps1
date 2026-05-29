﻿# ==============================================================================
# 卸载脚本: 停止上报并清理所有本地文件和计划任务
# ==============================================================================

$TASK_NAME = "Company_IP_Tracker"
$INSTALL_DIR = "C:\ProgramData\Company_Network"
$LOG_FILE = "$env:TEMP\uninstall_debug.log"

function Write-ULog($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try { [System.IO.File]::AppendAllText($LOG_FILE, "$ts $msg`r`n", [System.Text.Encoding]::UTF8) } catch {}
}

Write-ULog "=== uninstall.ps1 开始 ==="

# 1. 停止正在运行的任务实例
$r = schtasks /End /TN $TASK_NAME 2>&1
Write-ULog "schtasks /End: $r"

# 2. 强制结束相关 PowerShell 进程
Get-Process -Name powershell -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*report.ps1*" -or $_.CommandLine -like "*Company_Network*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-ULog "进程清理完成"

# 3. 删除计划任务
$r = schtasks /Delete /TN $TASK_NAME /F 2>&1
Write-ULog "schtasks /Delete: $r"

# 4. 删除安装目录及所有文件
if (Test-Path $INSTALL_DIR) {
    Remove-Item $INSTALL_DIR -Recurse -Force -ErrorAction SilentlyContinue
    Write-ULog "第一次删除目录完成"
}

# 5. 二次确认
if (Test-Path $INSTALL_DIR) {
    Get-ChildItem $INSTALL_DIR -Force | ForEach-Object {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $INSTALL_DIR -Force -Recurse -ErrorAction SilentlyContinue
    Write-ULog "第二次删除目录完成"
}

# 6. 最终检查
if (Test-Path $INSTALL_DIR) {
    Write-ULog "WARNING: 目录仍然存在"
} else {
    Write-ULog "目录已删除"
}

$schtask = schtasks /Query /TN $TASK_NAME 2>&1
Write-ULog "最终任务状态: $schtask"
Write-ULog "=== uninstall.ps1 完成 ==="
