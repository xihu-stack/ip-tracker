import os
from datetime import datetime, timedelta
from ipaddress import ip_address
from typing import Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, IpRecord
from services.ip_location import ip_to_city

router = APIRouter(prefix="/api", tags=["report"])

# 可选的上报共享密钥：只有设置了环境变量 IP_TRACKER_REPORT_SECRET 才启用校验。
# 不设置 = 完全不校验，已部署的旧客户端无感知；等全部客户端换上带令牌的
# deploy.ps1 后，再在服务端配置该变量开启校验（见 docs/运维手册.md）。
REPORT_SECRET = os.getenv("IP_TRACKER_REPORT_SECRET", "").strip()


class ReportRequest(BaseModel):
    hostname: str
    ip: str
    city: Optional[str] = ""
    lat: Optional[Union[float, str]] = None
    lon: Optional[Union[float, str]] = None

    @field_validator("hostname")
    @classmethod
    def check_hostname(cls, v):
        v = (v or "").strip()
        if not v or len(v) > 128:
            raise ValueError("hostname 不能为空且不超过 128 字符")
        return v

    @field_validator("ip")
    @classmethod
    def check_ip(cls, v):
        v = (v or "").strip()
        try:
            ip_address(v)
        except ValueError:
            raise ValueError("ip 不是合法的 IP 地址")
        return v

    @field_validator("lat", "lon", mode="before")
    @classmethod
    def parse_numeric(cls, v):
        if v is None or v == "" or v == "None":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


@router.post("/report")
def report(data: ReportRequest, db: Session = Depends(get_db), x_report_token: Optional[str] = Header(default=None)):
    if REPORT_SECRET and x_report_token != REPORT_SECRET:
        raise HTTPException(status_code=403, detail="上报令牌无效")
    # 根据 hostname 查找或创建员工
    employee = db.query(Employee).filter(Employee.hostname == data.hostname).first()
    if not employee:
        employee = Employee(hostname=data.hostname)
        db.add(employee)
        db.flush()

    # 每次上报都更新 last_seen_at（用于在线状态判断）
    employee.last_seen_at = datetime.now()

    # 始终使用服务端查询（支持区级精度），客户端传来的仅作备用
    city = data.city
    latitude = data.lat
    longitude = data.lon

    location = ip_to_city(data.ip)
    if location.get("city") and location["city"] != "未知":
        city = location["city"]
        latitude = location.get("lat")
        longitude = location.get("lon")
    elif not city or city == "":
        city = location.get("city", "未知")
        latitude = location.get("lat")
        longitude = location.get("lon")

    # 去重：同一员工同一 IP 1小时内不新增记录
    recent = db.query(IpRecord).filter(
        IpRecord.employee_id == employee.id,
        IpRecord.ip == data.ip,
        IpRecord.reported_at >= datetime.now() - timedelta(hours=1)
    ).first()
    if recent:
        # 去重不新增记录，但更新定位信息（可能查到了更精确的区级数据/新坐标）
        if city and city != "未知" and recent.city != city:
            recent.city = city
        if latitude is not None and longitude is not None:
            recent.latitude = latitude
            recent.longitude = longitude
        db.commit()
        return {"status": "ok", "message": "duplicate", "city": city}

    record = IpRecord(
        employee_id=employee.id,
        ip=data.ip,
        city=city,
        latitude=latitude,
        longitude=longitude,
        reported_at=datetime.now()
    )
    db.add(record)
    db.commit()

    return {"status": "ok", "message": "reported", "city": city}
