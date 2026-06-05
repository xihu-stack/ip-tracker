from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, IpRecord, Admin
from auth import get_current_admin

router = APIRouter(prefix="/api", tags=["query"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    total_employees = db.query(func.count(Employee.id)).scalar()
    total_records = db.query(func.count(IpRecord.id)).scalar()

    # 用 Employee.last_seen_at 判断在线（每次上报都更新，不受历史去重影响）
    threshold = datetime.now() - timedelta(minutes=20)
    online_count = db.query(func.count(Employee.id)).filter(
        Employee.last_seen_at >= threshold
    ).scalar()

    offline_count = total_employees - online_count

    # 今日新增记录数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    day_records = db.query(func.count(IpRecord.id)).filter(
        IpRecord.reported_at >= today_start
    ).scalar()

    # 离线设备列表
    offline_employees = db.query(Employee).filter(
        Employee.last_seen_at < threshold
    ).all()
    offline_list = []
    for emp in offline_employees:
        latest = db.query(IpRecord).filter(IpRecord.employee_id == emp.id).order_by(IpRecord.reported_at.desc()).first()
        offline_list.append({
            "id": emp.id,
            "hostname": emp.hostname,
            "name": emp.name or "",
            "latest_ip": latest.ip if latest else "-",
            "latest_city": latest.city if latest else "-",
            "latest_time": emp.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if emp.last_seen_at else (latest.reported_at.strftime("%Y-%m-%d %H:%M:%S") if latest else "-"),
            "status": "never" if not latest else "offline"
        })

    return {
        "total_employees": total_employees,
        "total_records": total_records,
        "online_count": online_count,
        "offline_count": offline_count,
        "day_records": day_records,
        "offline_list": offline_list
    }


@router.get("/employees")
def list_employees(
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin)
):
    query = db.query(Employee)
    if search:
        query = query.filter(
            (Employee.hostname.contains(search)) | (Employee.name.contains(search))
        )

    total = query.count()
    employees = query.order_by(Employee.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for emp in employees:
        latest = db.query(IpRecord).filter(IpRecord.employee_id == emp.id).order_by(IpRecord.reported_at.desc()).first()
        threshold = datetime.now() - timedelta(minutes=20)
        is_online = emp.last_seen_at and emp.last_seen_at >= ten_min_ago
        result.append({
            "id": emp.id,
            "hostname": emp.hostname,
            "name": emp.name or "",
            "created_at": emp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "latest_ip": latest.ip if latest else "-",
            "latest_city": latest.city if latest else "-",
            "latest_time": emp.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if emp.last_seen_at else (latest.reported_at.strftime("%Y-%m-%d %H:%M:%S") if latest else "-"),
            "is_online": is_online
        })

    return {"total": total, "page": page, "page_size": page_size, "data": result}


@router.get("/employees/{employee_id}/records")
def employee_records(
    employee_id: int,
    start_date: str = Query(default=""),
    end_date: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    query = db.query(IpRecord).filter(IpRecord.employee_id == employee_id)
    if start_date:
        query = query.filter(IpRecord.reported_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(IpRecord.reported_at < end)

    total = query.count()
    records = query.order_by(IpRecord.reported_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    data = [{
        "id": r.id,
        "ip": r.ip,
        "city": r.city,
        "reported_at": r.reported_at.strftime("%Y-%m-%d %H:%M:%S")
    } for r in records]

    return {
        "employee": {"id": employee.id, "hostname": employee.hostname, "name": employee.name or ""},
        "total": total, "page": page, "page_size": page_size, "data": data
    }


@router.get("/map-data")
def map_data(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """返回地图散点数据：按城市聚合，包含经纬度和设备数量"""
    # 获取每个员工最新一条记录
    from sqlalchemy import and_
    subquery = db.query(
        IpRecord.employee_id,
        func.max(IpRecord.reported_at).label("max_time")
    ).group_by(IpRecord.employee_id).subquery()

    latest_records = db.query(IpRecord).join(
        subquery,
        and_(
            IpRecord.employee_id == subquery.c.employee_id,
            IpRecord.reported_at == subquery.c.max_time
        )
    ).all()

    # 预加载员工信息
    emp_cache = {}
    for emp in db.query(Employee).all():
        emp_cache[emp.id] = emp

    # 按城市聚合
    city_map = {}
    for r in latest_records:
        if not r.city or r.city == "未知" or r.latitude is None or r.longitude is None:
            continue
        key = r.city
        if key not in city_map:
            city_map[key] = {
                "city": r.city,
                "lat": r.latitude,
                "lng": r.longitude,
                "count": 0,
                "employees": []
            }
        city_map[key]["count"] += 1
        emp = emp_cache.get(r.employee_id)
        if emp:
            label = f"{emp.name} ({emp.hostname})" if emp.name else emp.hostname
            city_map[key]["employees"].append(label)

    return list(city_map.values())


class UpdateEmployeeRequest(BaseModel):
    name: str


@router.put("/employees/{employee_id}")
def update_employee(employee_id: int, data: UpdateEmployeeRequest, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    employee.name = data.name
    db.commit()
    return {"status": "ok", "id": employee.id, "hostname": employee.hostname, "name": employee.name}


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.query(IpRecord).filter(IpRecord.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return {"status": "ok", "message": f"已删除员工 {employee.hostname} 及其所有记录"}
