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

$SERVER_URL = "http://192.168.30.67:8000/api/report"
$TASK_NAME = "Company_IP_Tracker"

# 统一使用标准的公共本地路径，避免 SYSTEM 账户与普通用户 AppData 错位
$INSTALL_DIR = "C:\ProgramData\Company_Network"
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}

# 1. 写入常驻上报脚本（客户端直接获取IP+城市+经纬度）
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
    '    $ipSources = @("https://api.ipify.org", "https://checkip.amazonaws.com", "https://ifconfig.me/ip")'
    '    foreach ($url in $ipSources) {'
    '        try {'
    '            $ip = (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).Content.Trim()'
    '            if ($ip -match ''^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'') { break }'
    '            $ip = $null'
    '        } catch { continue }'
    '    }'
    '    if (-not $ip) { Write-Log "ERROR: Get IP Failed"; exit 1 }'
    '    $city = ""; $lat = ""; $lon = ""'
    '    try {'
    '        # 升级为 https，防止内网拦截与 DNS 污染'
    '        $geoUrl = "https://ip-api.com/json/" + $ip + "?lang=zh-CN&fields=status,regionName,city,lat,lon"'
    '        $geoResp = (Invoke-WebRequest -Uri $geoUrl -UseBasicParsing -TimeoutSec 5).Content'
    '        '
    '        # 采用全面兼容旧版 PowerShell 3.0/4.0/5.0+ 的健壮对象解析方案'
    '        $geo = ConvertFrom-Json $geoResp'
    '        if ($geo -and $geo.status -eq "success") {'
    '            $region = if ($geo.regionName) { $geo.regionName } else { "" }'
    '            $c = if ($geo.city) { $geo.city } else { "" }'
    '            '
    '            if ($region -and $c) {'
    '                $city = if ($region -eq $c) { $c } else { "$region-$c" }'
    '            } else { $city = "$region$c" }'
    '            '
    '            $lat = if ($geo.lat) { [string]$geo.lat } else { "" }'
    '            $lon = if ($geo.lon) { [string]$geo.lon } else { "" }'
    '        }'
    '    } catch { Write-Log "WARN: GeoIP query failed, fallback to pure IP" }'
    '    '
    '    # 构建标准密实 JSON 并上报'
    '    $body = @{hostname=$hostname; ip=$ip; city=$city; lat=$lat; lon=$lon} | ConvertTo-Json -Compress'
    '    Invoke-WebRequest -Uri $SERVER_URL -Method Post -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 | Out-Null'
    '    Write-Log "OK: $hostname -> $ip [$city] ($lat,$lon)"'
    '} catch { Write-Log "ERROR: $($_.Exception.Message)"; exit 1 }'
)
[System.IO.File]::WriteAllLines($scriptPath, $lines, [System.Text.Encoding]::UTF8)
Write-DeployLog "常驻脚本已写入: $scriptPath"

# 2. 强力创建计划任务 (显式指定以 SYSTEM 凭据非交互运行，并增加 /V1 核心兼容，彻底防止卡死)
schtasks /Delete /TN $TASK_NAME /F 2>$null | Out-Null
$taskResult = schtasks /Create /TN $TASK_NAME /TR "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$scriptPath`"" /SC MINUTE /MO 10 /RU "SYSTEM" /V1 /F 2>&1
Write-DeployLog "计划任务配置结果: $taskResult"

# 3. 执行首次上报
Write-DeployLog "正在执行首次同步上报..."
& $scriptPath

Write-DeployLog "=== deploy.ps1 执行完毕，准备退出 ==="