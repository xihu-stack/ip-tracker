# ==============================================================================
# 脚本名称: deploy.ps1
# 安全优化版：彻底解决 IP-guard 推送时卡在“准备安装”的进程死锁问题
# 升级功能：本地自主解析 GeoIP 增强地理位置定位，全 Windows 系统版本完美兼容
# ==============================================================================

$DEPLOY_LOG = "$env:TEMP\deploy_debug.log"
function Write-DeployLog($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $user = "$env:COMPUTERNAME\$env:USERNAME"
    try {
        [System.IO.File]::AppendAllText($DEPLOY_LOG, "$ts [$user] $msg`r`n", [System.Text.Encoding]::UTF8)
    } catch {}
}
Write-DeployLog "=== deploy.ps1 开始执行 ==="

# 内网部署用 8000 端口，公网部署改为 9000 端口
$SERVER_URL = "http://112.81.86.182:9000/api/report"
$TASK_NAME = "Company_IP_Tracker"

# 统一使用标准的公共本地路径，避免 SYSTEM 账户与普通用户 AppData 错位
$INSTALL_DIR = "C:\ProgramData\Company_Network"
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}

# 1. 写入常驻上报脚本（使用国内 IP 服务，兼容 SD-WAN 环境）
$scriptPath = "$INSTALL_DIR\report.ps1"
$lines = @(
    '$SERVER_URL = "' + $SERVER_URL + '"'
    '$LOG_FILE = "$env:TEMP\ip_report.log"'
    'function Write-Log($msg) {'
    '    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"'
    '    try { [System.IO.File]::AppendAllText($LOG_FILE, "$timestamp $msg`r`n", [System.Text.Encoding]::UTF8) } catch {}'
    '}'
    'try {'
    '    $hostname = $env:COMPUTERNAME'
    '    $ip = $null'
    '    # 国内 IP 查询源，SD-WAN 环境下国内流量不走海外出口'
    '    $ipSources = @("http://members.3322.org/dyndns/getip", "http://ip.3322.net", "https://myip.ipip.net")'
    '    foreach ($url in $ipSources) {'
    '        try {'
    '            $resp = (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).Content.Trim()'
    '            # myip.ipip.net 返回格式为 "当前 IP：x.x.x.x  来自于：..."'
    '            if ($resp -match ''(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'') { $ip = $Matches[1]; break }'
    '        } catch { continue }'
    '    }'
    '    if (-not $ip) { Write-Log "ERROR: Get IP Failed"; exit 1 }'
    '    $city = ""; $lat = ""; $lon = ""'
    '    try {'
    '        # ip-api.com 根据查询的 IP 返回归属地，不受本机出口影响'
    '        $geoUrl = "http://ip-api.com/json/" + $ip + "?lang=zh-CN&fields=status,regionName,city,lat,lon"'
    '        $geoResp = (Invoke-WebRequest -Uri $geoUrl -UseBasicParsing -TimeoutSec 5).Content'
    '        $geo = ConvertFrom-Json $geoResp'
    '        if ($geo -and $geo.status -eq "success") {'
    '            $region = if ($geo.regionName) { $geo.regionName } else { "" }'
    '            $c = if ($geo.city) { $geo.city } else { "" }'
    '            if ($region -and $c) {'
    '                $city = if ($region -eq $c) { $c } else { "$region-$c" }'
    '            } else { $city = "$region$c" }'
    '            $lat = if ($geo.lat) { [string]$geo.lat } else { "" }'
    '            $lon = if ($geo.lon) { [string]$geo.lon } else { "" }'
    '        }'
    '    } catch { Write-Log "WARN: GeoIP query failed, fallback to pure IP" }'
    '    $body = @{hostname=$hostname; ip=$ip; city=$city; lat=$lat; lon=$lon} | ConvertTo-Json -Compress'
    '    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)'
    '    Invoke-WebRequest -Uri $SERVER_URL -Method Post -Body $bodyBytes -ContentType "application/json; charset=utf-8" -UseBasicParsing -TimeoutSec 10 | Out-Null'
    '    Write-Log "OK: $hostname -> $ip [$city] ($lat,$lon)"'
    '} catch { Write-Log "ERROR: $($_.Exception.Message)"; exit 1 }'
)
[System.IO.File]::WriteAllLines($scriptPath, $lines, [System.Text.Encoding]::UTF8)
Write-DeployLog "常驻脚本已写入: $scriptPath"

# 2. 创建计划任务 (以 SYSTEM 账户非交互运行，无条件执行)
schtasks /Delete /TN $TASK_NAME /F 2>$null | Out-Null
# 用 PowerShell 创建任务，绕过 schtasks 不支持高级设置的限制
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$scriptPath`""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $TASK_NAME -Action $Action -Trigger $Trigger -Settings $Settings -User "SYSTEM" -Force | Out-Null
Write-DeployLog "计划任务配置完成（不受电源/空闲限制，错过即补跑）"

# 3. 执行首次上报
Write-DeployLog "正在执行首次同步上报..."
& $scriptPath

Write-DeployLog "=== deploy.ps1 执行完毕，准备退出 ==="