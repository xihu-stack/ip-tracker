#!/bin/bash
# ==============================================================================
# IP 定位追踪平台 — 一键部署脚本
# 用法: sudo bash install.sh [端口]
# 示例: sudo bash install.sh          # 默认 8000 端口
#       sudo bash install.sh 9000     # 自定义 9000 端口
# ==============================================================================

set -e

APP_DIR="/opt/ip-tracker"
PORT=${1:-8000}
PYTHON=python3

echo "============================================"
echo "   IP 定位追踪平台 — 一键部署"
echo "   安装目录: $APP_DIR"
echo "   监听端口: $PORT"
echo "============================================"

# ---------- 0. 检测是否 root ----------
if [ "$EUID" -ne 0 ]; then
    echo "[错误] 请使用 root 用户运行: sudo bash install.sh"
    exit 1
fi

# ---------- 1. 安装系统依赖 ----------
echo ""
echo "[1/5] 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip
elif command -v dnf &> /dev/null; then
    dnf install -y python3 python3-pip
else
    echo "[警告] 未检测到包管理器，请手动安装 Python 3"
fi

# ---------- 2. 准备文件 ----------
echo "[2/5] 准备应用文件..."

# 获取脚本所在目录（支持直接克隆后运行）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检测 main.py 的实际位置
if [ -f "$SCRIPT_DIR/server/main.py" ]; then
    # 仓库原始结构：server/main.py
    MAIN_PY="$SCRIPT_DIR/server/main.py"
else
    # 复制后的结构：main.py 在根目录
    MAIN_PY="$SCRIPT_DIR/main.py"
fi

# 如果已在目标目录运行，直接使用；否则复制过去
if [ "$SCRIPT_DIR" = "$APP_DIR" ]; then
    echo "   → 已在 $APP_DIR，跳过复制"
else
    mkdir -p $APP_DIR
    cp -r "$SCRIPT_DIR/server/"* $APP_DIR/
    mkdir -p $APP_DIR/frontend/dist
    if [ -d "$SCRIPT_DIR/frontend/dist" ]; then
        cp -r "$SCRIPT_DIR/frontend/dist/"* $APP_DIR/frontend/dist/
    else
        echo "[警告] 未找到前端构建产物，前端界面将不可用"
    fi
    mkdir -p $APP_DIR/client
    cp -r "$SCRIPT_DIR/client/"* $APP_DIR/client/ 2>/dev/null || true
    echo "   → 文件已复制到 $APP_DIR"
    MAIN_PY="$APP_DIR/main.py"
fi

echo "   → 入口文件: $MAIN_PY"

# ---------- 3. 创建虚拟环境 & 安装依赖 ----------
echo "[3/5] 安装 Python 依赖..."
cd $APP_DIR
$PYTHON -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet fastapi uvicorn sqlalchemy
echo "   → 依赖安装完成"

# ---------- 4. 配置 systemd 服务 ----------
echo "[4/5] 配置 systemd 服务..."
cat > /etc/systemd/system/ip-tracker.service <<EOF
[Unit]
Description=IP Tracker Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $MAIN_PY
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ip-tracker

echo "   → 服务已注册"

# ---------- 5. 启动服务 ----------
echo "[5/5] 启动服务..."
systemctl restart ip-tracker
sleep 2

if systemctl is-active --quiet ip-tracker; then
    echo ""
    echo "============================================"
    echo "   ✅ 部署成功！"
    echo ""
    echo "   访问地址: http://<服务器IP>:$PORT"
    echo ""
    echo "   常用命令:"
    echo "     systemctl status ip-tracker    # 查看状态"
    echo "     systemctl restart ip-tracker   # 重启"
    echo "     systemctl stop ip-tracker      # 停止"
    echo "     journalctl -u ip-tracker -f    # 查看日志"
    echo "============================================"
else
    echo ""
    echo "[错误] 服务启动失败，查看日志:"
    journalctl -u ip-tracker --no-pager -n 20
    exit 1
fi
