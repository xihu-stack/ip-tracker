#!/bin/bash
# ==============================================================================
# IP 定位追踪平台 — 上报口 HTTPS 一键开启脚本
#
# 给公网上报口 9000 配置 Let's Encrypt 证书：
#   - 9000 变为 HTTPS（其余路径仍 403，只放行 /api/report）
#   - 已部署的 HTTP 客户端无需改动：nginx 对误用 HTTP 的请求返回 307 跳转（保留 POST）
#   - 自动注册续期钩子（certbot 定时续期时临时停/启 nginx）
#
# 用法（服务器需有指向本机的域名，且 80 端口可公网访问）:
#   sudo bash enable_https.sh report.example.com [邮箱]
# 示例:
#   sudo bash enable_https.sh report.example.com admin@example.com
# ==============================================================================

set -e

DOMAIN=$1
EMAIL=${2:-}
if [ -z "$DOMAIN" ]; then
    echo "[错误] 用法: sudo bash enable_https.sh <域名> [邮箱]"
    exit 1
fi
if [ "$EUID" -ne 0 ]; then
    echo "[错误] 请使用 root 运行: sudo bash enable_https.sh $DOMAIN"
    exit 1
fi

# ---------- 1. 安装 certbot ----------
echo "[1/4] 安装 certbot..."
if command -v apt-get &> /dev/null; then
    apt-get install -y -qq certbot
elif command -v yum &> /dev/null; then
    yum install -y certbot
elif command -v dnf &> /dev/null; then
    dnf install -y certbot
else
    echo "[错误] 未检测到包管理器，请手动安装 certbot 后重试"
    exit 1
fi

# ---------- 2. 签发证书（standalone 需要 80 端口，临时停 nginx） ----------
echo "[2/4] 签发证书（域名: $DOMAIN）..."
EMAIL_ARG="--register-unsafely-without-email"
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="-m $EMAIL"
fi
systemctl stop nginx
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos $EMAIL_ARG
systemctl start nginx

# ---------- 3. 重写上报口配置为 HTTPS ----------
echo "[3/4] 配置 nginx HTTPS..."
cat > /etc/nginx/conf.d/ip-tracker.conf <<NGINX
server {
    listen 9000 ssl;
    server_name $DOMAIN;
    server_tokens off;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 仅代理客户端上报接口
    location /api/report {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
    }

    # 其他路径返回干净页面
    location / {
        default_type application/json;
        return 403 '{"status":"error","message":"Access Denied"}';
    }

    # 旧客户端仍用 http:// 打 9000 时返回 497，307 跳转到 https（保留 POST 方法和请求体）
    error_page 497 =307 https://\$host:9000\$request_uri;
}
NGINX

# 续期钩子：证书续期时 standalone 需要 80 端口
mkdir -p /etc/letsencrypt/renewal-hooks/pre /etc/letsencrypt/renewal-hooks/deploy
printf '#!/bin/bash\nsystemctl stop nginx\n' > /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh
printf '#!/bin/bash\nsystemctl start nginx\n' > /etc/letsencrypt/renewal-hooks/deploy/start-nginx.sh
chmod +x /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh /etc/letsencrypt/renewal-hooks/deploy/start-nginx.sh

# ---------- 4. 检查并重载 ----------
nginx -t && systemctl reload nginx

echo ""
echo "============================================"
echo "   ✅ HTTPS 已开启"
echo ""
echo "   新上报地址: https://$DOMAIN:9000/api/report"
echo ""
echo "   · 已部署客户端无需改动（http 请求会被 307 自动跳转）"
echo "   · 新部署建议 deploy.ps1 的 SERVER_URL 直接填 https 地址"
echo "   · 证书自动续期（certbot 定时任务 + 停启 nginx 钩子）"
echo "   · 防火墙/安全组需放行 9000（TCP）"
echo "============================================"
