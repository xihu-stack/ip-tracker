from datetime import datetime, timedelta
import threading
import time

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, IpRecord, Admin
from auth import get_current_admin
from services.ip_location import sane_city_label

router = APIRouter(prefix="/api", tags=["query"])

# 失联判定：超过 30 天未上报视为失联（区别于普通离线，多为离职/重装设备）
STALE_DAYS = 30

# 窗口函数能力探测：SQLite < 3.25（如 CentOS 7 自带 3.7）不支持，需降级查询
_window_fn_support = None


def _window_fn_ok(db: Session) -> bool:
    global _window_fn_support
    if _window_fn_support is None:
        try:
            db.execute(text("SELECT row_number() OVER (ORDER BY 1) FROM sqlite_master LIMIT 1"))
            _window_fn_support = True
        except Exception:
            _window_fn_support = False
            print("[db] 当前 SQLite 不支持窗口函数，最新记录查询使用兼容模式（结果一致，稍慢）")
    return _window_fn_support


def _latest_by_employee(db: Session) -> dict:
    """每个员工的最新记录。优先一条窗口函数 SQL；老版本 SQLite 自动降级为
    max(reported_at) 连接查询（结果一致，稍慢）。"""
    if _window_fn_ok(db):
        rn = func.row_number().over(
            partition_by=IpRecord.employee_id,
            order_by=IpRecord.reported_at.desc()
        ).label("rn")
        sub = db.query(
            IpRecord.employee_id, IpRecord.ip, IpRecord.city, IpRecord.city_source, IpRecord.reported_at, rn
        ).subquery()
        return {row.employee_id: row for row in db.query(sub).filter(sub.c.rn == 1).all()}

    mx = db.query(
        IpRecord.employee_id, func.max(IpRecord.reported_at).label("mx")
    ).group_by(IpRecord.employee_id).subquery()
    rows = db.query(IpRecord).join(
        mx, and_(IpRecord.employee_id == mx.c.employee_id, IpRecord.reported_at == mx.c.mx)
    ).all()
    return {r.employee_id: r for r in rows}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    total_employees = db.query(func.count(Employee.id)).scalar()
    total_records = db.query(func.count(IpRecord.id)).scalar()

    now = datetime.now()
    # 用 Employee.last_seen_at 判断在线（每次上报都更新，不受历史去重影响）
    threshold = now - timedelta(minutes=20)
    stale_threshold = now - timedelta(days=STALE_DAYS)
    online_count = db.query(func.count(Employee.id)).filter(
        Employee.last_seen_at >= threshold
    ).scalar()

    offline_count = total_employees - online_count

    # 今日新增记录数
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_records = db.query(func.count(IpRecord.id)).filter(
        IpRecord.reported_at >= today_start
    ).scalar()

    # 最近 24 小时逐小时上报量（仪表盘"今日上报"卡片迷你趋势）
    hour_rows = db.query(
        func.strftime("%Y-%m-%d %H:00", IpRecord.reported_at).label("h"),
        func.count(IpRecord.id)
    ).filter(IpRecord.reported_at >= now - timedelta(hours=24)).group_by("h").all()
    hour_counts = {r[0]: r[1] for r in hour_rows}
    hourly = []
    for i in range(24, 0, -1):
        bucket = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        hourly.append({"hour": bucket.hour, "count": hour_counts.get(bucket.strftime("%Y-%m-%d %H:00"), 0)})

    # 离线设备列表（最新记录用窗口函数一次取出）
    offline_employees = db.query(Employee).filter(
        Employee.last_seen_at < threshold
    ).all()
    latest_map = _latest_by_employee(db)
    offline_list = []
    for emp in offline_employees:
        latest = latest_map.get(emp.id)
        offline_list.append({
            "id": emp.id,
            "hostname": emp.hostname,
            "name": emp.name or "",
            "latest_ip": latest.ip if latest else "-",
            "latest_city": latest.city if latest else "-",
            "latest_city_source": (latest.city_source if latest else "") or "",
            "latest_time": emp.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if emp.last_seen_at else (latest.reported_at.strftime("%Y-%m-%d %H:%M:%S") if latest else "-"),
            "status": "never" if not latest else ("stale" if emp.last_seen_at and emp.last_seen_at < stale_threshold else "offline")
        })

    return {
        "total_employees": total_employees,
        "total_records": total_records,
        "online_count": online_count,
        "offline_count": offline_count,
        "day_records": day_records,
        "hourly": hourly,
        "offline_list": offline_list
    }


@router.get("/employees")
def list_employees(
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
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

    now = datetime.now()
    threshold = now - timedelta(minutes=20)
    stale_threshold = now - timedelta(days=STALE_DAYS)
    latest_map = _latest_by_employee(db)
    result = []
    for emp in employees:
        latest = latest_map.get(emp.id)
        result.append({
            "id": emp.id,
            "hostname": emp.hostname,
            "name": emp.name or "",
            "base_city": emp.base_city or "",
            "created_at": emp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "latest_ip": latest.ip if latest else "-",
            "latest_city": latest.city if latest else "-",
            "latest_city_source": (latest.city_source if latest else "") or "",
            "latest_time": emp.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if emp.last_seen_at else (latest.reported_at.strftime("%Y-%m-%d %H:%M:%S") if latest else "-"),
            "is_online": bool(emp.last_seen_at and emp.last_seen_at >= threshold),
            "is_stale": bool(emp.last_seen_at and emp.last_seen_at < stale_threshold)
        })

    return {"total": total, "page": page, "page_size": page_size, "data": result}


def _parse_date(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{field} 格式应为 YYYY-MM-DD")


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
        query = query.filter(IpRecord.reported_at >= _parse_date(start_date, "start_date"))
    if end_date:
        end = _parse_date(end_date, "end_date") + timedelta(days=1)
        query = query.filter(IpRecord.reported_at < end)

    total = query.count()
    records = query.order_by(IpRecord.reported_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    data = [{
        "id": r.id,
        "ip": r.ip,
        "city": r.city,
        "city_source": r.city_source or "",
        "reported_at": r.reported_at.strftime("%Y-%m-%d %H:%M:%S")
    } for r in records]

    return {
        "employee": {"id": employee.id, "hostname": employee.hostname, "name": employee.name or ""},
        "total": total, "page": page, "page_size": page_size, "data": data
    }


# map-data 结果缓存 30 秒：仪表盘每 30 秒轮询一次，设备多时避免每次全表聚合
_map_cache = {"ts": 0.0, "data": None}
_MAP_CACHE_TTL = 30


@router.get("/map-data")
def map_data(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """返回地图散点数据：按城市聚合，包含经纬度和设备数量"""
    if _map_cache["data"] is not None and time.time() - _map_cache["ts"] < _MAP_CACHE_TTL:
        return _map_cache["data"]
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

    # 按城市聚合；无法定位（城市未知或缺坐标）的单独返回，不再静默丢弃
    city_map = {}
    unmapped = {}
    for r in latest_records:
        if not r.city or r.city == "未知":
            unmapped["未知"] = unmapped.get("未知", 0) + 1
            continue
        if r.latitude is None or r.longitude is None:
            unmapped[r.city] = unmapped.get(r.city, 0) + 1
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

    result = {
        "points": list(city_map.values()),
        "unmapped": [
            {"city": k, "count": v} for k, v in sorted(unmapped.items(), key=lambda x: -x[1])
        ],
    }
    _map_cache.update(ts=time.time(), data=result)
    return result


class UpdateEmployeeRequest(BaseModel):
    name: str
    base_city: str = ""   # 不传或空字符串 = 清空驻地


@router.put("/employees/{employee_id}")
def update_employee(employee_id: int, data: UpdateEmployeeRequest, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    employee.name = data.name
    employee.base_city = (data.base_city or "").strip()
    db.commit()
    return {"status": "ok", "id": employee.id, "hostname": employee.hostname, "name": employee.name, "base_city": employee.base_city}


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.query(IpRecord).filter(IpRecord.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return {"status": "ok", "message": f"已删除员工 {employee.hostname} 及其所有记录"}


def _valid_city(city):
    return bool(city) and city != "未知" and city != "-"


@router.get("/location-stats")
def location_stats(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """人员位置统计：重点输出当前不在驻地办公的人员 + 最近位置变更记录。"""
    now = datetime.now()
    employees = db.query(Employee).all()
    latest_map = _latest_by_employee(db)

    summary = {"total": len(employees), "base_set": 0, "away": 0, "home": 0, "unknown": 0, "no_base": 0}
    away_list = []

    for emp in employees:
        base = (emp.base_city or "").strip()
        latest = latest_map.get(emp.id)
        if not base or not latest:
            summary["no_base"] += 1
            continue
        summary["base_set"] += 1
        cur = latest.city or ""
        if not _valid_city(cur):
            summary["unknown"] += 1
            continue
        if cur == base:
            summary["home"] += 1
            continue

        # 异地办公：回溯最近记录，找到当前这次"离开驻地"的起点
        # （记录已按 1 小时/IP 变更去重，城市变化即视为位置变更）
        summary["away"] += 1
        recs = db.query(IpRecord).filter(IpRecord.employee_id == emp.id)\
            .order_by(IpRecord.reported_at.desc()).limit(120).all()
        away_since = None
        for r in recs:  # 从新到旧
            if r.city == base:
                break
            if _valid_city(r.city):
                away_since = r.reported_at
        away_list.append({
            "id": emp.id,
            "name": emp.name or "",
            "hostname": emp.hostname,
            "base_city": base,
            "current_city": cur,
            "current_ip": latest.ip or "-",
            "away_since": away_since.strftime("%Y-%m-%d %H:%M") if away_since else None,
            "away_hours": round((now - away_since).total_seconds() / 3600, 1) if away_since else None,
        })

    # 最近 7 天位置变更事件（相邻记录城市不同即一次变更，"未知"跳过）
    since = now - timedelta(days=7)
    changes = []
    for emp in employees:
        recs = db.query(IpRecord).filter(
            IpRecord.employee_id == emp.id,
            IpRecord.reported_at >= since - timedelta(days=1)
        ).order_by(IpRecord.reported_at.desc()).all()
        # 取窗口起点之前最后一条记录作为对照基准
        prev_city = None
        prev = db.query(IpRecord).filter(
            IpRecord.employee_id == emp.id, IpRecord.reported_at < since - timedelta(days=1)
        ).order_by(IpRecord.reported_at.desc()).first()
        if prev:
            prev_city = prev.city if _valid_city(prev.city) else None
        for r in reversed(recs):  # 从旧到新
            if not _valid_city(r.city):
                continue
            if prev_city and r.city != prev_city:
                changes.append({
                    "time": r.reported_at.strftime("%Y-%m-%d %H:%M"),
                    "name": emp.name or "",
                    "hostname": emp.hostname,
                    "from_city": prev_city,
                    "to_city": r.city,
                    "is_away": bool((emp.base_city or "").strip()) and r.city != emp.base_city,
                })
            prev_city = r.city

    changes.sort(key=lambda c: c["time"], reverse=True)
    away_list.sort(key=lambda a: a["away_hours"] or 0, reverse=True)

    return {
        "summary": summary,
        "away_list": away_list,
        "changes": changes[:100],
    }


# ==================== 归属地数据体检与一键修正 ====================

_geo_cleanup = {"running": False, "total": 0, "done": 0, "updated": 0, "failed": 0,
                "started_at": "", "finished_at": "", "message": ""}


def _is_abnormal_city(city: str) -> bool:
    """异常城市：不是合法城市标签且不是"未知"（乱码碎片、空值等）。"""
    city = city or ""
    return city != "未知" and not sane_city_label(city)


def _abnormal_ips(db: Session) -> list:
    pairs = db.query(IpRecord.ip, IpRecord.city).distinct().all()
    return sorted({ip for ip, city in pairs if _is_abnormal_city(city)})


@router.get("/geo/health")
def geo_health(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """统计归属地异常的数据量（乱码城市等），供系统设置页展示。"""
    ips = _abnormal_ips(db)
    records = db.query(func.count(IpRecord.id)).filter(IpRecord.ip.in_(ips)).scalar() if ips else 0
    return {
        "abnormal_ips": len(ips),
        "abnormal_records": records,
        "cleanup": {k: _geo_cleanup[k] for k in ("running", "total", "done", "updated", "failed", "message")},
    }


def _run_geo_cleanup(ips: list):
    from database import SessionLocal
    from services.ip_location import ip_to_city
    db = SessionLocal()
    try:
        for ip in ips:
            try:
                loc = ip_to_city(ip)
                new_city = loc.get("city", "未知")
                n = db.query(IpRecord).filter(IpRecord.ip == ip, IpRecord.city_source != "manual").update({
                    "city": new_city, "city_source": loc.get("source", ""), "latitude": loc.get("lat"), "longitude": loc.get("lon"),
                })
                db.commit()
                _geo_cleanup["updated"] += n
            except Exception:
                _geo_cleanup["failed"] += 1
                db.rollback()
            _geo_cleanup["done"] += 1
            time.sleep(0.4)   # 对外部数据源友好
        _geo_cleanup["message"] = f"完成：修正 {_geo_cleanup['updated']} 条，失败 {_geo_cleanup['failed']} 个 IP"
    finally:
        _geo_cleanup["running"] = False
        _geo_cleanup["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.close()


@router.post("/geo/cleanup")
def geo_cleanup_start(db: Session = Depends(get_db), _: Admin = Depends(get_current_admin)):
    """一键修正：后台线程重新解析所有异常城市的 IP 并更新历史记录。"""
    if _geo_cleanup["running"]:
        return {"status": "already_running", **{k: _geo_cleanup[k] for k in ("total", "done")}}
    ips = _abnormal_ips(db)
    if not ips:
        _geo_cleanup["message"] = "没有异常数据"
        return {"status": "ok", "message": "没有异常数据，无需修正", "total": 0}
    _geo_cleanup.update(running=True, total=len(ips), done=0, updated=0, failed=0, message="",
                        started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), finished_at="")
    threading.Thread(target=_run_geo_cleanup, args=(ips,), daemon=True).start()
    return {"status": "started", "total": len(ips),
            "message": f"开始修正 {len(ips)} 个 IP 的历史记录，请稍候（每个 IP 约 0.5 秒）"}
