import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import Admin

# -- 配置 --
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def _load_secret_key() -> str:
    """JWT 签名密钥：优先环境变量 IP_TRACKER_SECRET_KEY；
    否则首次启动生成随机密钥并保存到 server/.secret_key（权限 600，已加入 .gitignore）。
    不再使用写死在代码里的默认值——仓库是公开的，硬编码密钥会被用来伪造管理员 token。"""
    env_key = os.getenv("IP_TRACKER_SECRET_KEY")
    if env_key:
        return env_key

    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secret_key")
    try:
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    except OSError:
        pass

    key = secrets.token_hex(32)
    try:
        fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(key)
        return key
    except OSError:
        # 目录只读等异常：退化为进程内临时密钥，重启后管理员需重新登录
        print("[auth] 警告：密钥文件写入失败，使用临时密钥")
        return key


SECRET_KEY = _load_secret_key()

# -- 密码哈希 --
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# -- JWT --
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        raise credentials_exception
    return admin
