import json
import os
import re
import secrets
import time
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Admin
from auth import verify_password, hash_password, create_access_token, get_current_admin

router = APIRouter(prefix="/api", tags=["auth"])

# ==================== SSO / OAuth2 统一门户登录（可选） ====================
# 标准 OAuth2 授权码流程，兼容 Keycloak / Authentik / Casdoor / Authing / 钉钉等。
# 环境变量（全部配置后才启用）：
#   OAUTH_ENABLED=1
#   OAUTH_AUTH_URL / OAUTH_TOKEN_URL / OAUTH_USERINFO_URL   # 提供商三个端点
#   OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET
#   OAUTH_SCOPE（默认 openid profile email）
#   OAUTH_REDIRECT_URI（默认按请求地址推导：<后台地址>/api/auth/callback）


def _load_oauth():
    if os.getenv("OAUTH_ENABLED", "").strip().lower() not in ("1", "true", "yes"):
        return None
    conf = {
        "client_id": os.getenv("OAUTH_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("OAUTH_CLIENT_SECRET", "").strip(),
        "auth_url": os.getenv("OAUTH_AUTH_URL", "").strip(),
        "token_url": os.getenv("OAUTH_TOKEN_URL", "").strip(),
        "userinfo_url": os.getenv("OAUTH_USERINFO_URL", "").strip(),
        "scope": os.getenv("OAUTH_SCOPE", "openid profile email"),
        "redirect_uri": os.getenv("OAUTH_REDIRECT_URI", "").strip(),
    }
    if not (conf["client_id"] and conf["auth_url"] and conf["token_url"]):
        print("[oauth] OAUTH_ENABLED=1 但缺少 CLIENT_ID/AUTH_URL/TOKEN_URL，SSO 未启用")
        return None
    return conf


OAUTH = _load_oauth()
_states = {}           # state -> {"redirect": 目标路径, "exp": 过期时间}
_STATE_TTL = 600


def _sso_username(info: dict) -> str:
    """从 userinfo 里取用户名，兼容常见字段，并限制到 Admin.username 允许的长度。"""
    for key in ("preferred_username", "username", "login", "sub", "email", "name"):
        val = info.get(key)
        if val:
            name = re.sub(r"[^\w.@-]", "_", str(val)).strip("_")
            return name[:64]
    return ""


def _clean_states():
    now = time.time()
    for k in [k for k, v in _states.items() if v["exp"] < now]:
        _states.pop(k, None)


@router.get("/auth/config")
def auth_config():
    """登录页据此决定是否展示/自动跳转 SSO。"""
    return {"sso_enabled": bool(OAUTH)}


@router.get("/auth/sso-login")
def sso_login(redirect: str = "/", request: Request = None):
    if not OAUTH:
        raise HTTPException(status_code=404, detail="SSO 未配置")
    # 只允许站内路径，防开放跳转
    if not redirect.startswith("/") or redirect.startswith("//"):
        redirect = "/"
    _clean_states()
    state = secrets.token_urlsafe(24)
    _states[state] = {"redirect": redirect, "exp": time.time() + _STATE_TTL}
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": OAUTH["client_id"],
        "redirect_uri": OAUTH["redirect_uri"] or f"{request.base_url}api/auth/callback",
        "scope": OAUTH["scope"],
        "state": state,
    })
    return RedirectResponse(f"{OAUTH['auth_url']}?{params}")


@router.get("/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = "", db: Session = Depends(get_db)):
    if not OAUTH:
        raise HTTPException(status_code=404, detail="SSO 未配置")
    front_base = str(request.base_url)  # 例如 http://ip:8000/

    def fail(reason: str):
        return RedirectResponse(f"{front_base}sso?error={urllib.parse.quote(reason)}")

    rec = _states.pop(state, None)
    if not code or not rec or rec["exp"] < time.time():
        return fail("登录状态已过期，请重新登录")

    redirect_uri = OAUTH["redirect_uri"] or f"{request.base_url}api/auth/callback"
    try:
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "client_id": OAUTH["client_id"],
            "client_secret": OAUTH["client_secret"],
            "redirect_uri": redirect_uri,
        }).encode()
        req = urllib.request.Request(
            OAUTH["token_url"], data=data,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        token_json = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        access_token = token_json.get("access_token", "")
        if not OAUTH["userinfo_url"] or not access_token:
            return fail("SSO 返回异常（缺 access_token）")
        req2 = urllib.request.Request(
            OAUTH["userinfo_url"],
            headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
        )
        info = json.loads(urllib.request.urlopen(req2, timeout=10).read().decode())
    except Exception as e:
        return fail(f"SSO 通信失败: {str(e)[:120]}")

    username = _sso_username(info)
    if not username:
        return fail("SSO 用户信息里没有可用的用户名")

    # 首次 SSO 登录自动开户（随机密码，密码登录方式对该账号不可用）
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        admin = Admin(username=username, hashed_password=hash_password(secrets.token_hex(16)))
        db.add(admin)
        db.commit()
        print(f"[oauth] SSO 用户首次登录，已自动创建管理员账号: {username}")

    token = create_access_token(data={"sub": username})
    return RedirectResponse(
        f"{front_base}sso?token={token}&redirect={urllib.parse.quote(rec['redirect'])}"
    )


# ==================== 账号密码登录 ====================

# 登录防爆破：同一 IP+用户名 连续失败 5 次锁定 10 分钟（内存计数，重启清零）
_LOGIN_FAILS = {}          # key -> [连续失败次数, 锁定截止时间戳]
_MAX_FAILS = 5
_LOCK_SECONDS = 600


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def _password_ok(password: str) -> bool:
    """新密码强度：至少 8 位，且同时包含字母和数字。"""
    return (
        len(password) >= 8
        and bool(re.search(r"[A-Za-z]", password))
        and bool(re.search(r"\d", password))
    )


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    key = f"{request.client.host}:{data.username}"
    rec = _LOGIN_FAILS.get(key)
    if rec and rec[1] > time.time():
        wait = int(rec[1] - time.time()) + 1
        raise HTTPException(status_code=429, detail=f"失败次数过多，请 {wait // 60} 分 {wait % 60} 秒后重试")

    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not verify_password(data.password, admin.hashed_password):
        rec = _LOGIN_FAILS.setdefault(key, [0, 0.0])
        rec[0] += 1
        if rec[0] >= _MAX_FAILS:
            rec[1] = time.time() + _LOCK_SECONDS
            rec[0] = 0
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    _LOGIN_FAILS.pop(key, None)
    token = create_access_token(data={"sub": admin.username})
    return {"access_token": token, "token_type": "bearer"}


@router.put("/change-password")
def change_password(data: ChangePasswordRequest, current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_admin.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not _password_ok(data.new_password):
        raise HTTPException(status_code=400, detail="新密码至少 8 位，且需同时包含字母和数字")
    current_admin.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"status": "ok", "message": "密码修改成功"}
