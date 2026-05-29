#!/bin/bash
# ==============================================================================
# IP-Tracker 一键部署脚本（Linux 服务器，无需 Nginx）
# 用法: sudo bash install.sh
# ==============================================================================

set -e

APP_DIR="/opt/ip-tracker"
PORT=9000
PYTHON=python3

echo "=== IP-Tracker 部署开始 ==="

# 1. 安装 Python
echo "[1/4] 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip
fi

# 2. 复制文件
echo "[2/4] 复制应用文件..."
mkdir -p $APP_DIR
cp -r server/* $APP_DIR/
mkdir -p $APP_DIR/frontend/dist
cp -r frontend/dist/* $APP_DIR/frontend/dist/

# 3. 安装 Python 依赖
echo "[3/4] 安装依赖..."
cd $APP_DIR
$PYTHON -m venv venv
source venv/bin/activate
pip install --quiet fastapi uvicorn sqlalchemy