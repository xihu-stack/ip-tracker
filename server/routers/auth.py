import re
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Admin
from auth import verify_password, hash_password, create_access_token, get_current_admin

router = APIRouter(prefix="/api", tags=["auth"])

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
