# SSO 对接最小示例（sso-demo）

与公司统一身份认证（http://10.4.128.19:8080）对接的**最小可运行示例**：
后端一个 Python 文件（FastAPI），前端一个网页（无构建依赖，双击/被后端托管即可）。
其他系统可直接复制这两个文件改造，完整版（页面配置、白名单管理、数据库等）见 ip-tracker 仓库。

## 目录

```
sso-demo/
├── README.md           # 本文件（对接步骤 + 踩坑清单）
├── backend/
│   ├── main.py         # 全部后端逻辑（约 200 行）
│   ├── requirements.txt
│   └── .env.example    # 配置模板
├── frontend/
│   └── index.html      # 全部前端逻辑（无框架、无构建）
└── fake_sso.py         # 本地模拟 SSO 服务器（联调用，不连真实门户也能跑通全流程）
```

## 快速开始（5 分钟）

### 1. 安装依赖并启动

```bash
cd backend
python -m venv venv && venv/bin/pip install -r requirements.txt   # Windows: venv\Scripts\pip
cp .env.example .env    # Windows: copy，然后编辑填入管理员发给你的 client_id/secret
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

### 2. 找认证中心管理员注册应用，拿到 client_id / client_secret

回调地址填：`http://你的地址:8001/api/auth/callback`（必须一字不差，见坑 4）

### 3. 填配置（.env）

```ini
OAUTH_ENABLED=1
OAUTH_CLIENT_ID=管理员分发
OAUTH_CLIENT_SECRET=管理员分发
OAUTH_AUTH_URL=http://10.4.128.19:8080/oauth2/authorize
OAUTH_TOKEN_URL=http://10.4.128.19:8080/oauth2/token
OAUTH_USERINFO_URL=http://10.4.128.19:8080/userinfo
OAUTH_LOGOUT_URL=http://10.4.128.19:8080/connect/logout
OAUTH_ALLOWED_USERS=     # 可选：允许登录的域账号，逗号分隔；留空=不限制
```

浏览器打开 `http://127.0.0.1:8001/` → 自动跳门户 → 域账号登录 → 回到示例页显示你的用户信息。

### 4. 本地联调（不连真实门户）

```bash
python fake_sso.py    # 模拟门户跑在 :9999，.env 三个地址改指 127.0.0.1:9999
```

## 集成到你的系统（改造指引）

1. 后端：把 `main.py` 里的 5 个路由拷进你的项目——`/api/auth/config`、`/api/auth/sso-login`、`/api/auth/callback`、`/api/auth/logout-notify`、受保护接口示例 `/api/me`
2. 把示例的 `issue_token / get_user` 换成你系统自己的会话机制（示例用的是自签 JWT）
3. 前端：`index.html` 的脚本拷走，核心只有四段——存 token、自动跳门户、"明确退出"标记、带 id_token_hint 登出
4. 让管理员登记**登出回调地址**：`http://你的地址:8001/api/auth/logout-notify`（门户退出时踢下你的系统）

## 踩坑清单（每条都是 ip-tracker 对接时真实踩过的）

1. **id_token 必须保存**：换令牌的响应里有 `id_token`，退出时作为 `id_token_hint` 传给
   `/connect/logout`，不带会被 400 拒绝、门户会话清不掉（示例已实现存取链路）
2. **post_logout_redirect_uri 需在门户登记**，未登记会 400；不确定就别带，让门户显示自己的登出页
3. **循环登录**：退出只清自己系统、门户会话还在 → 登录页又自动跳门户 → 秒登回来。
   解法：明确退出后记录标记（示例的 `logged_out`），登录页不再自动跳，直到用户点"重新登录"
4. **redirect_uri 严格匹配**：注册了域名就统一走域名访问，混用 IP 会 mismatch
5. **用户名取 `preferred_username`**（域账号）；如你的系统对接别的 SSO，把用户名字段做成可配置
6. **访问控制做两层**：门户侧给应用配授权名单 + 你系统侧白名单（`OAUTH_ALLOWED_USERS`），
   有敏感数据的系统尤其重要
7. **门户反向踢下线**：登记 `/api/auth/logout-notify`；无状态 JWT 用"吊销时间点"实现（示例已含）
8. **体验细节**：页面显示当前登录用户；"忘记密码"链到门户 `/pwd/`；管理员本地密码入口放独立路径

## 测试清单（上线前逐项过）

- [ ] 未登录访问 → 跳门户 → 登录后回到原页面
- [ ] 门户已登录 → 无感直达
- [ ] 本系统退出 → 不被门户会话自动登录回来
- [ ] 门户退出 → 本系统短时间内被踢下线（登记登出回调后）
- [ ] 白名单外用户被拒且不建档
- [ ] 域名 / IP 两种访问方式 redirect_uri 一致
