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
from models import Admin, Setting, TokenRevocation
from auth import verify_password, hash_password, create_access_token, get_current_admin

router = APIRouter(prefix="/api", tags=["auth"])

# ==================== SSO / OAuth2 统一门户登录（可选） ====================
# 标准 OAuth2 授权码流程，兼容 Keycloak / Authentik / Casdoor / Authing / 企业自建 SSO。
# 配置来源（优先级从高到低）：
#   1. 管理后台「系统设置 → SSO 配置」页面（存 settings 表，保存即生效，无需重启）
#   2. 环境变量（systemd Environment 或 /opt/ip-tracker/sso.conf）：
#      OAUTH_ENABLED / OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET / OAUTH_AUTH_URL /
#      OAUTH_TOKEN_URL / OAUTH_USERINFO_URL / OAUTH_SCOPE / OAUTH_REDIRECT_URI

SSO_SETTING_KEYS = (
    "sso_enabled", "sso_auth_url", "sso_token_url", "sso_userinfo_url",
    "sso_client_id", "sso_client_secret", "sso_scope", "sso_username_field",
    "sso_allowed_users", "sso_allowed_domains",
)


def _split_list(value: str):
    return [v.strip().lower() for v in re.split(r"[,;\n]+", value or "") if v.strip()]


def _sso_access_denied(rows: dict, username: str) -> str:
    """SSO 访问白名单：两个名单都为空 = 不限制；否则必须命中其一。
    用户名精确匹配（不区分大小写），域名匹配邮箱后缀（如 @huashen.bio）。"""
    allowed_users = _split_list(rows.get("sso_allowed_users", ""))
    allowed_domains = [d.lstrip("@").lower() for d in _split_list(rows.get("sso_allowed_domains", ""))]
    if not allowed_users and not allowed_domains:
        return ""
    name = username.lower()
    if name in allowed_users:
        return ""
    for d in allowed_domains:
        if name.endswith("@" + d):
            return ""
    return "该账号不在 SSO 访问白名单内，无权访问本系统（请联系管理员调整系统设置）"


def _load_env_oauth():
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
        "logout_url": os.getenv("OAUTH_LOGOUT_URL", "").strip(),
        "username_field": "",
    }
    if not (conf["client_id"] and conf["auth_url"] and conf["token_url"]):
        print("[oauth] OAUTH_ENABLED=1 但缺少 CLIENT_ID/AUTH_URL/TOKEN_URL，SSO 未启用")
        return None
    return conf


def get_oauth(db: Session):
    """取生效的 SSO 配置：后台页面配置(DB)优先，环境变量兜底。"""
    try:
        rows = {s.key: (s.value or "") for s in db.query(Setting).all()}
    except Exception:
        rows = {}
    if rows:
        if rows.get("sso_enabled") != "1":
            return None
        conf = {
            "client_id": rows.get("sso_client_id", ""),
            "client_secret": rows.get("sso_client_secret", ""),
            "auth_url": rows.get("sso_auth_url", ""),
            "token_url": rows.get("sso_token_url", ""),
            "userinfo_url": rows.get("sso_userinfo_url", ""),
            "scope": rows.get("sso_scope") or "openid profile email",
            "redirect_uri": "",
            "logout_url": rows.get("sso_logout_url", ""),
            "username_field": rows.get("sso_username_field", ""),
        }
        if conf["client_id"] and conf["auth_url"] and conf["token_url"]:
            return conf
        return None
    return _load_env_oauth()


_states = {}           # state -> {"redirect": 目标路径, "exp": 过期时间}
_STATE_TTL = 600


def _sso_username(info: dict, field: str = "") -> str:
    """从 userinfo 里取用户名：优先自定义字段（企业自建 SSO 常用 account/loginName 等），
    再按常见字段回退，并限制到 Admin.username 允许的长度。"""
    keys = (field, "preferred_username", "username", "login", "account", "sub", "email", "name")
    for key in keys:
        if not key:
            continue
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
def auth_config(db: Session = Depends(get_db)):
    """登录页据此决定是否展示/自动跳转 SSO；logout_url 供退出时做全局登出。"""
    oauth = get_oauth(db)
    return {
        "sso_enabled": bool(oauth),
        "logout_url": (oauth or {}).get("logout_url", ""),
    }


@router.get("/auth/sso-login")
def sso_login(redirect: str = "/", request: Request = None, db: Session = Depends(get_db)):
    oauth = get_oauth(db)
    if not oauth:
        raise HTTPException(status_code=404, detail="SSO 未配置")
    # 只允许站内路径，防开放跳转
    if not redirect.startswith("/") or redirect.startswith("//"):
        redirect = "/"
    _clean_states()
    state = secrets.token_urlsafe(24)
    _states[state] = {"redirect": redirect, "exp": time.time() + _STATE_TTL}
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": oauth["client_id"],
        "redirect_uri": oauth["redirect_uri"] or f"{request.base_url}api/auth/callback",
        "scope": oauth["scope"],
        "state": state,
    })
    return RedirectResponse(f"{oauth['auth_url']}?{params}")


@router.get("/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = "", db: Session = Depends(get_db)):
    oauth = get_oauth(db)
    if not oauth:
        raise HTTPException(status_code=404, detail="SSO 未配置")
    front_base = str(request.base_url)  # 例如 http://ip:8000/

    def fail(reason: str):
        return RedirectResponse(f"{front_base}sso?error={urllib.parse.quote(reason)}")

    rec = _states.pop(state, None)
    if not code or not rec or rec["exp"] < time.time():
        return fail("登录状态已过期，请重新登录")

    redirect_uri = oauth["redirect_uri"] or f"{request.base_url}api/auth/callback"
    try:
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "client_id": oauth["client_id"],
            "client_secret": oauth["client_secret"],
            "redirect_uri": redirect_uri,
        }).encode()
        req = urllib.request.Request(
            oauth["token_url"], data=data,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        token_json = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        access_token = token_json.get("access_token", "")
        if not oauth["userinfo_url"] or not access_token:
            return fail("SSO 返回异常（缺 access_token）")
        req2 = urllib.request.Request(
            oauth["userinfo_url"],
            headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
        )
        info = json.loads(urllib.request.urlopen(req2, timeout=10).read().decode())
    except Exception as e:
        return fail(f"SSO 通信失败: {str(e)[:120]}")

    username = _sso_username(info, oauth.get("username_field", ""))
    if not username:
        return fail("SSO 用户信息里没有可用的用户名（可在系统设置里调整用户名字段）")

    # 访问白名单（未配置 = 不限制）；拒绝时不自动开户
    rows = _get_settings(db)
    denied = _sso_access_denied(rows, username)
    if denied:
        print(f"[oauth] SSO 用户被白名单拒绝: {username}")
        return fail(denied)

    # 首次 SSO 登录自动开户（随机密码，密码登录方式对该账号不可用）
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        admin = Admin(username=username, hashed_password=hash_password(secrets.token_hex(16)))
        db.add(admin)
        db.commit()
        print(f"[oauth] SSO 用户首次登录，已自动创建管理员账号: {username}")

    token = create_access_token(data={"sub": username, "login": "sso"})
    # 透传 OIDC id_token：前端保存，退出时作为 id_token_hint 让门户正确清除全局会话
    id_token = token_json.get("id_token", "")
    extra = f"&id_token={urllib.parse.quote(id_token)}" if id_token else ""
    return RedirectResponse(
        f"{front_base}sso?token={token}&redirect={urllib.parse.quote(rec['redirect'])}{extra}"
    )


# ---------- 门户登出通知（全局单点登出的反方向：门户退出时踢下本系统会话） ----------

class LogoutNotifyRequest(BaseModel):
    username: str
    logoutAt: int = 0


@router.post("/auth/logout-notify")
def logout_notify(data: LogoutNotifyRequest, db: Session = Depends(get_db)):
    """接收统一门户的登出回调（应用管理 → 编辑应用 → 登出回调地址填本接口）。

    本系统使用无状态 JWT，"销毁本地会话"通过令牌吊销实现：
    记录该用户的吊销时间，早于该时间签发的令牌全部失效（前端 30 秒轮询内自动回到登录页）。
    """
    from datetime import datetime as _dt
    username = (data.username or "").strip()
    if not username:
        return {"status": "ignored", "message": "缺少 username"}
    now = _dt.now()
    rev = db.query(TokenRevocation).filter(TokenRevocation.username == username).first()
    if rev:
        rev.revoked_at = now
    else:
        db.add(TokenRevocation(username=username, revoked_at=now))
    db.commit()
    print(f"[oauth] 收到门户登出通知，已吊销本地令牌: {username} (logoutAt={data.logoutAt})")
    return {"status": "ok", "message": f"已吊销 {username} 的本地会话"}


# ---------- SSO 配置管理（后台「系统设置」页面用） ----------

class SsoSettingsRequest(BaseModel):
    sso_enabled: bool = False
    sso_auth_url: str = ""
    sso_token_url: str = ""
    sso_userinfo_url: str = ""
    sso_client_id: str = ""
    sso_client_secret: str = ""     # 留空 = 保留已保存的密钥
    sso_scope: str = "openid profile email"
    sso_username_field: str = ""
    sso_logout_url: str = ""    # 全局登出端点（OIDC end_session_endpoint），配置后"退出登录"会同时登出统一门户
    sso_allowed_users: str = ""     # 用户名白名单，逗号/换行分隔
    sso_allowed_domains: str = ""   # 邮箱后缀白名单，逗号分隔


def _get_settings(db: Session) -> dict:
    return {s.key: (s.value or "") for s in db.query(Setting).all()}


def _set_setting(db: Session, key: str, value: str):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))


@router.get("/settings/sso")
def get_sso_settings(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    rows = _get_settings(db)
    return {
        "sso_enabled": rows.get("sso_enabled") == "1",
        "sso_auth_url": rows.get("sso_auth_url", ""),
        "sso_token_url": rows.get("sso_token_url", ""),
        "sso_userinfo_url": rows.get("sso_userinfo_url", ""),
        "sso_client_id": rows.get("sso_client_id", ""),
        "sso_client_secret": "",
        "sso_has_secret": bool(rows.get("sso_client_secret")),
        "sso_scope": rows.get("sso_scope", "openid profile email"),
        "sso_username_field": rows.get("sso_username_field", ""),
        "sso_logout_url": rows.get("sso_logout_url", ""),
        "sso_allowed_users": rows.get("sso_allowed_users", ""),
        "sso_allowed_domains": rows.get("sso_allowed_domains", ""),
        # SSO 由服务器环境变量启用（页面尚未保存过配置）——此时保存会覆盖环境变量
        "sso_env_enabled": not rows and _load_env_oauth() is not None,
    }


@router.put("/settings/sso")
def put_sso_settings(data: SsoSettingsRequest, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    if data.sso_enabled:
        missing = [name for name, v in (
            ("授权地址", data.sso_auth_url), ("Token 地址", data.sso_token_url), ("客户端 ID", data.sso_client_id)
        ) if not v.strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"启用 SSO 需要填写：{'、'.join(missing)}")

    values = {
        "sso_enabled": "1" if data.sso_enabled else "0",
        "sso_auth_url": data.sso_auth_url.strip(),
        "sso_token_url": data.sso_token_url.strip(),
        "sso_userinfo_url": data.sso_userinfo_url.strip(),
        "sso_client_id": data.sso_client_id.strip(),
        "sso_scope": data.sso_scope.strip() or "openid profile email",
        "sso_username_field": data.sso_username_field.strip(),
        "sso_logout_url": data.sso_logout_url.strip(),
        "sso_allowed_users": data.sso_allowed_users.strip(),
        "sso_allowed_domains": data.sso_allowed_domains.strip(),
    }
    for k, v in values.items():
        _set_setting(db, k, v)
    # 密钥：只在填了新值时更新（避免回显/留空清掉）
    if data.sso_client_secret.strip():
        _set_setting(db, "sso_client_secret", data.sso_client_secret.strip())
    db.commit()
    return {"status": "ok", "message": "SSO 配置已保存，立即生效（无需重启服务）"}


@router.post("/settings/sso/test")
def test_sso_settings(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """逐个探测端点连通性（不发起真实登录）。"""
    import urllib.error
    oauth = get_oauth(db)
    if not oauth:
        return {"ok": False, "message": "SSO 未启用或配置不完整（已启用时需填授权地址/Token地址/客户端ID）"}

    results = {}
    for name in ("auth_url", "token_url", "userinfo_url"):
        url = oauth.get(name)
        if not url:
            results[name] = {"status": "未配置"}
            continue
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            urllib.request.urlopen(req, timeout=5)
            results[name] = {"status": "OK"}
        except urllib.error.HTTPError as e:
            # 端点存在但对空请求返回 4xx/5xx 属正常（如 405 不允许 GET）
            results[name] = {"status": f"可达（HTTP {e.code}）"}
        except Exception as e:
            results[name] = {"status": f"不可达：{str(e)[:80]}"}

    ok = all("不可达" not in r["status"] for r in results.values())
    return {"ok": ok, "results": results, "message": "全部端点可达" if ok else "存在不可达端点，请检查地址"}


# ---------- IP 归属地人工映射（系统设置页面用） ----------

class GeoSettingsRequest(BaseModel):
    ip_city_map: str = ""   # 每行一条：IP 或 CIDR 网段 + 空格 + 城市名


@router.get("/settings/geo")
def get_geo_settings(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    rows = _get_settings(db)
    return {"ip_city_map": rows.get("ip_city_map", "")}


@router.put("/settings/geo")
def put_geo_settings(data: GeoSettingsRequest, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    import ipaddress
    bad = []
    for line in (data.ip_city_map or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not parts[1].strip():
            bad.append(line)
            continue
        try:
            ipaddress.ip_network(parts[0], strict=False)
        except ValueError:
            bad.append(line)
    if bad:
        raise HTTPException(
            status_code=400,
            detail="以下行格式不正确（应为 IP或网段 + 空格 + 城市名，如 203.0.113.5 上海）：" + "；".join(bad[:3])
        )
    _set_setting(db, "ip_city_map", (data.ip_city_map or "").strip())
    db.commit()
    return {"status": "ok", "message": "映射已保存，约 30 秒内生效（命中的 IP 不再走在线查询）"}


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
    token = create_access_token(data={"sub": admin.username, "login": "local"})
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
