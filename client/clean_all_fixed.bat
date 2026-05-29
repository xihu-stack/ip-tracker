@echo off
:: ==============================================================================
:: 脚本名称: clean_all_fixed.bat
:: 适用环境: 适用于 IP-guard 软件分发 (SYSTEM 权限静默无感知运行)
:: 功能描述: 连续强杀触发器避免时间差撞车，强制粉碎常驻任务与 C:\ProgramData 落地文件
:: ==============================================================================
chcp 65001 >nul 2>&1

echo [1/3] 正在进入多轮强杀死循环触发器...
:: 第一轮尝试终止当前可能正在运行的任务实例
schtasks /End /TN "Company_IP_Tracker" /F >nul 2>&1

:: 极其关键：利用系统自带的 ping 实现 1.5 秒的微延时，完美错开高频触发器的到点撞车
ping 127.0.0.1 -n 2 >nul 2>&1

:: 第二轮强杀，确保彻底掐断僵尸进程
schtasks /End /TN "Company_IP_Tracker" /F >nul 2>&1

echo [2/3] 正在强制拔除计划任务外壳...
:: 使用 /F 参数在系统底层直接粉碎任务，无视任何 Session 0 的隐形质询
schtasks /Delete /TN "Company_IP_Tracker" /F >nul 2>&1

echo [3/3] 正在粉碎本地常驻脚本目录及日志...
:: 物理删除公共落地文件夹
if exist "C:\ProgramData\Company_Network" (
    rd /s /q "C:\ProgramData\Company_Network" >nul 2>&1
)

:: 清理残留的临时调试日志
if exist "%TEMP%\ip_report.log" del /f /q "%TEMP%\ip_report.log" >nul 2>&1
if exist "%TEMP%\deploy_debug.log" del /f /q "%TEMP%\deploy_debug.log" >nul 2>&1
if exist "%TEMP%\uninstall_debug.log" del /f /q "%TEMP%\uninstall_debug.log" >nul 2>&1

echo === 卸载清理彻底完成 ===
exit /b 0