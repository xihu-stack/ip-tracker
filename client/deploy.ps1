# ==============================================================================
# 脚本名称: deploy.ps1  (客户端 v2.0)
# 变更说明（相对 v1 已部署版本）:
#   1. 去掉客户端 ip-api.com 归属地查询——服务端三源交叉解析更强，且不再有境外请求和乱码来源
#   2. 上报带版本标识（body.cli = 2.0 / User-Agent），便于统计推送覆盖率
#   3. 日志自动轮转（超过 1MB 重新开始），不再无限增长
#   4. 上报失败自动重试一次
#   5. 支持上报令牌（$REPORT_TOKEN，留空=与当前服务器行为一致）
# 兼容性: 任务名/安装目录与 v1 相同，重推即原地升级，无需卸载
# ==============================================================================

$DEPLOY_LOG = "$env:TEMP\deploy_debug.log"
function Write-DeployLog($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $user = "$env:COMPUTERNAME\$env:USERNAME"
    try {
        [System.IO.File]::AppendAllText($DEPLOY_LOG, "$ts [$user] $msg`r`n", [System.Text.Encoding]::UTF8)
    } catch {}
}
Write-DeployLog "=== deploy.ps1 v2.0 开始执行 ==="

# 上报地址用域名：以后换服务器只需改 DNS 解析，客户端无需重新推送
# 内网部署用 8000 端口，公网部署用 9000 端口
$SERVER_URL = "http://iptracker.huashen.bio:9000/api/report"
# 上报令牌（可选）：与服务器环境变量 IP_TRACKER_REPORT_SECRET 配合使用。
# 留空 = 不带令牌，兼容当前未开启校验的服务器；填入后需在服务器同步配置才生效
$REPORT_TOKEN = ""
$CLIENT_VERSION = "2.0"
$TASK_NAME = "Company_IP_Tracker"

# 统一使用标准的公共本地路径，避免 SYSTEM 账户与普通用户 AppData 错位
$INSTALL_DIR = "C:\ProgramData\Company_Network"
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}

# 1. 写入常驻上报脚本（v2：仅上报主机名+公网IP，归属地由服务端解析）
$scriptPath = "$INSTALL_DIR\report.ps1"
$lines = @(
    '$SERVER_URL = "' + $SERVER_URL + '"'
    '$REPORT_TOKEN = "' + $REPORT_TOKEN + '"'
    '$CLIENT_VERSION = "' + $CLIENT_VERSION + '"'
    '$LOG_FILE = "$env:TEMP\ip_report.log"'
    'function Write-Log($msg) {'
    '    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"'
    '    try {'
    '        # 日志轮转：超过 1MB 重新开始'
    '        if ((Test-Path $LOG_FILE) -and ((Get-Item $LOG_FILE).Length -gt 1MB)) { Remove-Item $LOG_FILE -Force }'
    '        [System.IO.File]::AppendAllText($LOG_FILE, "$timestamp $msg`r`n", [System.Text.Encoding]::UTF8)'
    '    } catch {}'
    '}'
    'try {'
    '    $hostname = $env:COMPUTERNAME'
    '    $ip = $null'
    '    # 国内 IP 查询源，SD-WAN 环境下国内流量不走海外出口'
    '    $ipSources = @("http://members.3322.org/dyndns/getip", "http://ip.3322.net", "https://myip.ipip.net")'
    '    foreach ($url in $ipSources) {'
    '        try {'
    '            $resp = (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).Content.Trim()'
    '            if ($resp -match ''(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'') { $ip = $Matches[1]; break }'
    '        } catch { continue }'
    '    }'
    '    if (-not $ip) { Write-Log "ERROR: Get IP Failed"; exit 1 }'
    '    $body = @{hostname=$hostname; ip=$ip; cli=$CLIENT_VERSION} | ConvertTo-Json -Compress'
    '    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)'
    '    $headers = @{ "User-Agent" = "IPTracker-Client/$CLIENT_VERSION" }'
    '    if ($REPORT_TOKEN) { $headers["X-Report-Token"] = $REPORT_TOKEN }'
    '    $ok = $false'
    '    foreach ($attempt in 1..2) {'
    '        try {'
    '            Invoke-WebRequest -Uri $SERVER_URL -Method Post -Body $bodyBytes -ContentType "application/json; charset=utf-8" -Headers $headers -UseBasicParsing -TimeoutSec 10 | Out-Null'
    '            $ok = $true; break'
    '        } catch { Start-Sleep -Seconds 3 }'
    '    }'
    '    if ($ok) { Write-Log "OK: $hostname -> $ip (cli $CLIENT_VERSION)" }'
    '    else { Write-Log "ERROR: report failed after retries: $($_.Exception.Message)" }'
    '} catch { Write-Log "ERROR: $($_.Exception.Message)"; exit 1 }'
)
[System.IO.File]::WriteAllLines($scriptPath, $lines, [System.Text.Encoding]::UTF8)
Write-DeployLog "常驻脚本 v$CLIENT_VERSION 已写入: $scriptPath"

# 2. 创建计划任务 (以 SYSTEM 账户非交互运行，无条件执行；同名任务自动覆盖=原地升级)
schtasks /Delete /TN $TASK_NAME /F 2>$null | Out-Null
foreach ($legacy in @("IPTrackerReport")) {
    schtasks /Delete /TN $legacy /F 2>$null | Out-Null
}
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$scriptPath`""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $TASK_NAME -Action $Action -Trigger $Trigger -Settings $Settings -User "SYSTEM" -Force | Out-Null
Write-DeployLog "计划任务配置完成（每 10 分钟，原地升级）"

# 3. 执行首次上报
Write-DeployLog "正在执行首次同步上报..."
& $scriptPath

Write-DeployLog "=== deploy.ps1 v$CLIENT_VERSION 执行完毕 ==="
