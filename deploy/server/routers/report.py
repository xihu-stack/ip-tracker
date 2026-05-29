from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, IpRecord
from services.ip_location import ip_to_city

router = APIRouter(prefix="/api", tags=["report"])


class ReportRequest(BaseModel):
    hostname: str
    ip: str
    city: Optional[str] = ""
    lat: Optional[float] = None
    lon: Optional[float] = None


@router.post("/report")
def report(data: ReportRequest, db: Session = Depends(get_db)):
    # 根据 hostname 查找或创建员工
    employee = db.query(Employee).filter(Employee.hostname == data.hostname).first()
    if not employee:
        employee = Employee(hostname=data.hostname)
        db.add(employee)
        db.flush()

    # 优先使用客户端传来的城市和经纬度，没有则服务端查询
    city = data.city
    latitude = data.lat
    longitude = data.lon

    if not city or city == "":
        location = ip_to_city(data.ip)
        city = location["city"]
        latitude = location.get("lat")
        longitude = location.get("lon")

    # 去重：同一员工同一 IP 5分钟内不重复记录
    recent = db.query(IpRecord).filter(
        IpRecord.employee_id == employee.id,
        IpRecord.ip == data.ip,
        IpRecord.reported_at >= datetime.now() - timedelta(minutes=5)
    ).first()
    if recent:
        return {"status": "ok", "message": "duplicate"}

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
