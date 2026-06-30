# IP 定位追踪平台

企业内网 IP 定位追踪系统。自动采集终端设备的公网 IP 和地理位置，在管理后台展示设备在线状态、城市分布地图和历史轨迹。

## 项目结构

```
├── server/                 # FastAPI 后端
│   ├── main.py             # 入口，挂载静态文件
│   ├── database.py         # SQLAlchemy + SQLite 配置
│   ├── models.py           # ORM 模型
│   ├── cleanup_geo.py      # 历史归属地批量修正脚本（一次性）
│   ├── routers/
│   │   ├── report.py       # 客户端上报接口
│   │   └── query.py        # 查询接口（仪表盘、员工、地图）
│   └── services/
│       ├── ip_location.py  # IP → 城市（cip.cc 数据源）
│       └── city_coords.py  # 中国城市经纬度对照表
├── frontend/               # Vue 3 + Element Plus 前端
│   ├── src/                # 源码
│   └── dist/               # 构建产物（已提交，可直接部署）
├── client/                 # Windows 客户端部署脚本
│   ├── deploy.ps1          # 一键安装
│   └── clean_all_fixed.bat # 一键卸载
└── install.sh              # ⭐ Linux 一键部署脚本
```

## 一键部署（Linux）

在服务器上执行以下两条命令即可完成部署：

```bash
# 1. 克隆项目
git clone https://github.com/xihu-stack/ip-tracker.git

# 2. 一键部署（默认 8000 端口）
cd -ip-tracker
sudo bash install.sh
```

自定义端口：

```bash
sudo bash install.sh 9000    # 使用 9000 端口
```

脚本会自动完成：安装 Python → 复制文件 → 创建虚拟环境 → 安装依赖 → 配置 systemd 开机自启 → 启动服务。

部署完成后访问 `http://<服务器IP>:8000` 即可看到管理界面。

### 服务管理

```bash
systemctl status ip-tracker     # 查看状态
systemctl restart ip-tracker    # 重启
systemctl stop ip-tracker       # 停止
journalctl -u ip-tracker -f     # 查看实时日志
```

### 防火墙放行

```bash
# CentOS / RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Ubuntu
sudo ufw allow 8000/tcp
```

## 前端重新构建

如需修改前端代码后重新构建：

```bash
cd frontend
npm install
npm run build
```

然后将 `frontend/dist/` 的内容更新到服务器 `/opt/ip-tracker/frontend/dist/` 并重启服务即可。

## Windows 客户端部署

客户端需要在每台 Windows 电脑上安装，用于定时上报 IP。

### 一键安装

1. 从服务器下载脚本：`http://<服务器IP>:8000` 页面中有部署指引
2. 或直接使用仓库中的 `client/deploy.ps1`

修改 `deploy.ps1` 中的上报地址。**建议用域名**（以后换服务器只改 DNS 解析，客户端无需重新推送），并指向公网上报口：

```powershell
# 内网 8000 = 管理后台；公网 9000 = 客户端上报接口（仅放行 /api/report）
$SERVER_URL = "http://report.example.com:9000/api/report"
```

以管理员身份运行：

```powershell
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

脚本会自动：
- 安装上报脚本到 `C:\ProgramData\Company_Network\report.ps1`
- 创建计划任务，每 **10 分钟**自动上报 IP 和地理位置
- 立即执行一次上报

### 卸载客户端

```powershell
schtasks /Delete /TN "Company_IP_Tracker" /F
Remove-Item "C:\ProgramData\Company_Network" -Recurse -Force
```

## 定位数据源

服务器根据客户端上报的**公网 IP** 统一解析归属地（客户端传来的位置仅作备用）：

- **城市/区**：通过 [cip.cc](http://cip.cc) 查询，国内精确、无需 key。
- **经纬度**：由内置的中国城市经纬度对照表（`server/services/city_coords.py`）按城市给出，地图按城市打点。

切换数据源后，如需把历史记录的归属地也修正过来，在服务器上运行：

```bash
cd /opt/ip-tracker && python3 cleanup_geo.py   # 只更新 city/经纬度，不删历史记录
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/report` | 客户端上报 IP |
| GET | `/api/dashboard` | 仪表盘统计（在线/离线/总数） |
| GET | `/api/employees` | 员工列表（分页、搜索） |
| PUT | `/api/employees/{id}` | 更新员工姓名 |
| GET | `/api/employees/{id}/records` | 员工 IP 历史记录 |
| GET | `/api/map-data` | 地图散点数据（按城市聚合） |

## 技术栈

- **后端**：Python 3 + FastAPI + SQLAlchemy + SQLite
- **前端**：Vue 3 + Vite + Element Plus + ECharts
- **客户端**：Windows PowerShell 计划任务
- **定位数据源**：cip.cc（IP 归属地，国内精确）+ 内置城市经纬度表
