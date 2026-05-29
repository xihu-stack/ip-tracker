# IP 定位追踪平台

企业内网 IP 定位追踪系统。自动采集终端设备的公网 IP 和地理位置，在管理后台展示设备在线状态、城市分布地图和历史轨迹。

## 项目结构

```
├── server/                 # FastAPI 后端
│   ├── main.py             # 入口，挂载静态文件
│   ├── database.py         # SQLAlchemy + SQLite 配置
│   ├── models.py           # ORM 模型
│   ├── routers/
│   │   ├── report.py       # 客户端上报接口
│   │   └── query.py        # 查询接口（仪表盘、员工、地图）
│   └── services/
│       └── ip_location.py  # IP → 城市/经纬度查询
├── frontend/               # Vue 3 + Element Plus 前端
│   ├── src/                # 源码
│   └── dist/               # 构建产物（已提交，可直接部署）
├── client/                 # Windows 客户端部署脚本
├── install.sh              # ⭐ Linux 一键部署脚本
└── deploy/                 # 旧版打包文件
```

## 一键部署（Linux）

在服务器上执行以下两条命令即可完成部署：

```bash
# 1. 克隆项目
git clone https://github.com/xihu-stack/-ip-tracker.git

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

修改 `deploy.ps1` 中的服务器地址：

```powershell
$SERVER_URL = "http://<你的服务器IP>:8000/api/report"
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
