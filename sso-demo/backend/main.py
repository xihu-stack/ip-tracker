"""SSO 对接最小后端示例（FastAPI，单文件）。

路由清单：
  GET  /                        前端页面
  GET  /api/auth/config         前端据此决定是否自动跳门户
  GET  /api/auth/sso-login      302 到统一门户授权地址（带 state 防 CSRF）
  GET  /api/auth/callback       门户回跳：换令牌 -> 取用户信息 -> 签发本系统 JWT
  GET  /api/me                  受保护接口示例（校验本系统 JWT + 吊销检查）
  POST /api/auth/logout-notify  门户登出回调：吊销该用户全部本系统令牌

运行：venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
"""
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from jose import JWTError, jwt

app = FastAPI(title="SSO Demo")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(APP_DIR, "..", "frontend", "index.html")

# ---------- 配置（来自环境变量 / .env） ----------


def _conf() -> dict:
    return {
        "enabled": os.getenv("OAUTH_ENABLED", "0") == "1",
        "client_id": os.getenv("OAUTH_CLIENT_ID", ""),
        "client_secret": os.getenv("OAUTH_CLIENT_SECRET", ""),
        "auth_url": os.getenv("OAUTH_AUTH_URL", ""),
        "token_url": os.getenv("OAUTH_TOKEN_URL", ""),
        "userinfo_url": os.getenv("OAUTH_USERINFO_URL", ""),
        "logout_url": os.getenv("OAUTH_LOGOUT_URL", ""),
        "scope": os.getenv("OAUTH_SCOPE", "openid profile email"),
        "allowed_users": [u.strip().lower() for u in os.getenv("OAUTH_ALLOWED_USERS", "").split(",") if u.strip()],
    }


# 本系统自签 JWT 的密钥（生产请固定配置，重启不掉线）
JWT_SECRET = os.getenv("APP_JWT_SECRET") or secrets.token_hex(32)
JWT_TTL_HOURS = 24

_states = {}    # state -> {"redirect": 站内路径, "exp": 过期时间}，10 分钟有效
_revoked = {}   # username -> 吊销时间点（logout-notify 用）


def _issue_token(info: dict) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": info.get("preferred_username") or info.get("sub") or "",
         "name": info.get("name", ""), "email": info.get("email", ""),
         "iat": now, "exp": now + JWT_TTL_HOURS * 3600},
        JWT_SECRET, algorithm="HS256")


def _get_user(request: Request) -> Optional[dict]:
    """校验本系统 JWT + 吊销检查。返回用户信息或 None。"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        return None
    revoked = _revoked.get(payload.get("sub"))
    if revoked and int(payload.get("iat") or 0) <= revoked:
        return None  # 已被门户登出通知吊销
    return payload


# ---------- 页面与公共接口 ----------


@app.get("/")
def index():
    return FileResponse(FRONTEND)


@app.get("/api/auth/config")
def auth_config():
    c = _conf()
    ok = c["enabled"] and c["client_id"] and c["auth_url"] and c["token_url"]
    return {"sso_enabled": bool(ok), "logout_url": c["logout_url"] if ok else ""}


# ---------- 登录流程 ----------


@app.get("/api/auth/sso-login")
def sso_login(redirect: str = "/", request: Request = None):
    c = _conf()
    if not (c["enabled"] and c["auth_url"]):
        return RedirectResponse("/?error=sso_not_configured")
    if not redirect.startswith("/") or redirect.startswith("//"):
        redirect = "/"
    state = secrets.token_urlsafe(24)
    _states[state] = {"redirect": redirect, "exp": time.time() + 600}
    # 清理过期 state
    for k in [k for k, v in _states.items() if v["exp"] < time.time()]:
        _states.pop(k, None)
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": c["client_id"],
        "redirect_uri": f"{request.base_url}api/auth/callback",
        "scope": c["scope"], "state": state,
    })
    return RedirectResponse(f"{c['auth_url']}?{params}")


@app.get("/api/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = ""):
    c = _conf()
    front = str(request.base_url)

    def fail(msg):
        return RedirectResponse(f"/?error={urllib.parse.quote(msg)}")

    rec = _states.pop(state, None)
    if not code or not rec or rec["exp"] < time.time():
        return fail("登录状态已过期，请重新登录")

    # 1. code 换令牌（secret 用 POST 参数；门户也支持 Basic 认证）
    try:
        body = urllib.parse.urlencode({
            "grant_type": "authorization_code", "code": code,
            "client_id": c["client_id"], "client_secret": c["client_secret"],
            "redirect_uri": f"{request.base_url}api/auth/callback",
        }).encode()
        req = urllib.request.Request(c["token_url"], data=body,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"})
        tokens = json.loads(urllib.request.urlopen(req, timeout=10).read())
        access_token, id_token = tokens.get("access_token", ""), tokens.get("id_token", "")
        if not access_token:
            return fail("门户未返回 access_token")
    except Exception as e:
        return fail(f"换令牌失败: {str(e)[:100]}")

    # 2. 取用户信息（Bearer 令牌）
    try:
        req = urllib.request.Request(c["userinfo_url"],
            headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"})
        info = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception as e:
        return fail(f"取用户信息失败: {str(e)[:100]}")

    username = (info.get("preferred_username") or info.get("sub") or "").strip()
    if not username:
        return fail("用户信息里没有可用的用户名")

    # 3. 白名单检查（可选；不配置 = 不限制）
    if c["allowed_users"] and username.lower() not in c["allowed_users"]:
        return fail("该账号不在访问白名单内")

    # 4. 签发本系统令牌；id_token 透传给前端保存（退出时作为 id_token_hint）
    token = _issue_token(info)
    extra = f"&id_token={urllib.parse.quote(id_token)}" if id_token else ""
    return RedirectResponse(f"/?token={token}&redirect={urllib.parse.quote(rec['redirect'])}{extra}")


# ---------- 受保护接口示例 ----------


@app.get("/api/me")
def me(request: Request):
    user = _get_user(request)
    if not user:
        return {"error": "unauthorized"}  # 生产中应返回 401
    return {"username": user["sub"], "name": user.get("name", ""), "email": user.get("email", "")}


# ---------- 门户登出回调（门户退出时踢下本系统会话） ----------


@app.post("/api/auth/logout-notify")
async def logout_notify(request: Request):
    """登记到认证中心「应用管理 → 登出回调地址」。
    请求体：{"username":"xxx","logoutAt":169...}"""
    try:
        data = json.loads(await request.body())
    except Exception:
        return {"status": "ignored"}
    username = (data.get("username") or "").strip()
    if username:
        _revoked[username] = int(time.time())
        print(f"[sso] 门户登出通知，已吊销本地令牌: {username}")
    return {"status": "ok"}
