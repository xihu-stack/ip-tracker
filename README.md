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
│   ├── src/
│   │   ├── views/          # Dashboard / Employees / History / Guide
│   │   ├── api/            # Axios 请求封装
│   │   └── router/         # Vue Router
│   ├── vite.config.js
│   └── package.json
├── client/                 # Windows 客户端部署脚本
│   └── deploy.ps1          # 一键安装计划任务（每 10 分钟上报）
└── deploy/                 # 打包好的部署文件（可直接上传）
```

## 服务端部署（Linux）

### 1. 安装依赖

```bash
# CentOS / RHEL
sudo yum install -y python3 python3-pip

# Ubuntu / Debian
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
```

### 2. 上传代码

将 `server/` 和 `frontend/dist/` 上传到服务器：

```bash
# 创建目录
sudo mkdir -p /opt/ip-tracker/frontend/dist

# 上传（在本地执行）
scp -r server/* root@<服务器IP>:/opt/ip-tracker/
scp -r frontend/dist/* root@<服务器IP>:/opt/ip-tracker/frontend/dist/
```

### 3. 创建虚拟环境并安装 Python 依赖

```bash
cd /opt/ip-tracker
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy
```

### 4. 测试运行

```bash
cd /opt/ip-tracker
source venv/bin/activate
python main.py
```

默认监听 `0.0.0.0:8000`，浏览器访问 `http://<服务器IP>:8000`。

### 5. 配置 systemd 开机自启

创建服务文件：

```bash
sudo tee /etc/systemd/system/ip-tracker.service > /dev/null <<EOF
[Unit]
Description=IP Tracker Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ip-tracker
ExecStart=/opt/ip-tracker/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ip-tracker
sudo systemctl status ip-tracker
```

常用管理命令：

```bash
sudo systemctl restart ip-tracker   # 重启
sudo systemctl stop ip-tracker      # 停止
sudo journalctl -u ip-tracker -f    # 查看实时日志
```

### 6. 防火墙放行

```bash
# CentOS / RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Ubuntu (ufw)
sudo ufw allow 8000/tcp
```

## 前端构建

如果需要修改前端后重新构建：

```bash
cd frontend
npm install
npm run build
```

构建产物在 `frontend/dist/`，上传到服务器的 `/opt/ip-tracker/frontend/dist/` 即可。

> 后端 `main.py` 会自动检测 `frontend/dist/` 目录，存在则以静态文件方式挂载，无需 Nginx。

## Windows 客户端部署

### 方式一：PowerShell 一键部署

将 `client/deploy.ps1` 中的服务器地址改为你自己的：

```powershell
$SERVER_URL = "http://<你的服务器IP>:8000/api/report"
```

然后在目标机器上以管理员身份运行：

```powershell
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

脚本会自动：
- 安装上报脚本到 `C:\ProgramData\Company_Network\report.ps1`
- 创建 Windows 计划任务，每 **10 分钟**自动上报 IP 和地理位置
- 立即执行一次上报

### 方式二：手动创建计划任务

```powershell
# 1. 下载 report.ps1 到本地
# 2. 修改其中的 $SERVER_URL
# 3. 创建计划任务
schtasks /Create /TN "IP_Tracker" /TR "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File C:\path\to\report.ps1" /SC MINUTE /MO 10 /RU "SYSTEM" /F
```

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
