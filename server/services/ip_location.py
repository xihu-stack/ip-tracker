import gzip
import ipaddress
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    from .city_coords import get_city_coord, _normalize
except ImportError:  # 兼容直接以模块方式运行（如一次性脚本）
    from city_coords import get_city_coord, _normalize


_cache = {}
_SUCCESS_TTL = 3600   # 成功结果缓存 1 小时（同一 IP 期间不再请求外部）
_FAILURE_TTL = 300    # 失败结果只缓存 5 分钟，便于尽快重试

# 地址/数据三行里需要过滤掉的噪音词：国家名、运营商、分隔符
# （某些移动 IP，cip.cc 只知道"中国移动"，不过滤就会把"移动"误当成城市）
_NOISE_TOKENS = {
    "中国", "China", "china", "PRC",
    "移动", "联通", "电信", "铁通", "广电", "鹏博士", "教育网", "长城",
    "华数", "方正", "世纪互联", "中移", "中国移动", "中国联通", "中国电信",
    "|",
}


def _decode_body(raw: bytes) -> str:
    """数据源编码不固定（cip.cc/pconline 有时返回 GBK 中文），先严格按 UTF-8 解，
    失败则按 GB18030（GBK 超集）解，避免中文城市被拼成乱码碎片（如 'Ϻ'/'㽭ʡ'）。"""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", errors="ignore")


def _read_text(resp) -> str:
    """读取响应并处理 gzip 压缩（个别 CDN 会强制压缩，urllib 不会自动解压，
    压缩字节按 GB18030 强解会产生 'M' 之类的乱码碎片）。"""
    raw = resp.read()
    if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    return _decode_body(raw)


def _query_cip_cc(ip: str):
    """数据源 1：cip.cc，文本格式，免 key。返回 (province, city) 或 None。

    格式示例：
        地址\t: 中国 江苏 南京
        数据三\t: 中国 江苏省 南京市
    """
    try:
        url = f"http://cip.cc/{ip}"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = _read_text(resp)
    except Exception:
        # 网络错误 / 503 限流 / 超时等：交由后续数据源兜底
        return None

    def _parts_of(line_prefix: str):
        for line in text.splitlines():
            if line_prefix in line and ":" in line:
                val = line.split(":", 1)[1].strip()
                return [p for p in val.split() if p and p not in _NOISE_TOKENS]
        return []

    province = ""
    city = ""
    addr = _parts_of("地址")
    if addr:
        province = addr[0]
        if len(addr) > 1:
            city = addr[1]
    if not city:
        data3 = _parts_of("数据三")
        if data3:
            province = data3[0]
            if len(data3) > 1:
                city = data3[1]
    province = _normalize(province)
    city = _normalize(city)
    if not province and not city:
        return None
    if not city:
        city = province
    return province, city


def _query_pconline(ip: str):
    """数据源 2：太平洋 pconline，JSON 格式，免 key。

    返回示例：{"pro":"江苏省","city":"南京市","addr":"江苏省南京市 电信","err":""}
    """
    try:
        url = f"https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true"
        req = urllib.request.Request(url, headers={"User-Agent": "IPTracker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = _read_text(resp)
        data = json.loads(text)
        if data.get("err"):
            return None
        province = _normalize(data.get("pro") or "")
        city = _normalize(data.get("city") or "")
        if not province and not city:
            return None
        if not city:
            city = province
        return province, city
    except Exception:
        return None


def _query_ip_api_com(ip: str):
    """数据源 3：ip-api.com，JSON 格式，免 key（免费 HTTP 接口限 45 次/分钟，
    有 1 小时结果缓存 + 并发查询，实际压力远低于限额）。"""
    try:
        url = f"http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,regionName,city"
        req = urllib.request.Request(url, headers={"User-Agent": "IPTracker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(_read_text(resp))
        if data.get("status") != "success":
            return None
        province = _normalize(data.get("regionName") or "")
        city = _normalize(data.get("city") or "")
        if not province and not city:
            return None
        if not city:
            city = province
        return province, city
    except Exception:
        return None


# 数据源（名称, 函数）。要加更多源，往这里加一项即可。
_SOURCES = (
    ("cip.cc", _query_cip_cc),
    ("pconline", _query_pconline),
    ("ip-api", _query_ip_api_com),
)

# 三源并发查询，避免串行等待（单源超时 5s，并发后总耗时不超过 5s）
_query_pool = ThreadPoolExecutor(max_workers=3)


def _query_all(ip: str):
    futures = [(name, _query_pool.submit(fn, ip)) for name, fn in _SOURCES]
    out = []
    for name, fut in futures:
        try:
            out.append((name, fut.result(timeout=6)))
        except Exception:
            out.append((name, None))
    return out


def _resolve(ip: str):
    """三源并发 + 交叉校验：
    - 至少两个源给出相同城市 → 采纳共识（减少单个 IP 库登记错误）
    - 无共识 → 按源优先级（cip.cc > pconline > ip-api）取第一个给出城市的
    - 都只给省级 → 取优先级最高的省级结果兜底
    """
    valid = []
    fallback = None
    for name, geo in _query_all(ip):
        if not geo:
            continue
        province, city = geo
        if city and city != province:
            valid.append((name, province, city))
        elif fallback is None and city:
            fallback = (province, city)

    if valid:
        counts = {}
        for _, _, c in valid:
            counts[c] = counts.get(c, 0) + 1
        best = max(counts, key=counts.get)
        if counts[best] >= 2:
            for _, p, c in valid:
                if c == best and p != c:
                    return p, c
        for want, _ in _SOURCES:            # 按源优先级
            for name, p, c in valid:
                if name == want:
                    return p, c
        return valid[0][1], valid[0][2]
    return fallback


# ---------- 人工映射（企业固定出口 IP 钉住城市，100% 准确） ----------

_override_cache = {"ts": 0.0, "nets": None}
_OVERRIDE_TTL = 30   # 映射表 30 秒重读一次，改完设置很快生效


def _load_overrides():
    """从 settings 表读 ip_city_map（每行一条：IP或CIDR网段 + 空格 + 城市名）。"""
    now = time.time()
    if _override_cache["nets"] is not None and now - _override_cache["ts"] < _OVERRIDE_TTL:
        return _override_cache["nets"]
    nets = []
    try:
        from database import SessionLocal
        from models import Setting
        db = SessionLocal()
        try:
            row = db.query(Setting).filter(Setting.key == "ip_city_map").first()
            raw = (row.value or "") if row else ""
        finally:
            db.close()
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or " " not in line:
                continue
            cidr, _, city = line.partition(" ")
            try:
                nets.append((ipaddress.ip_network(cidr.strip(), strict=False), city.strip()))
            except ValueError:
                continue
    except Exception:
        nets = []
    _override_cache.update(ts=now, nets=nets)
    return nets


def _manual_lookup(ip: str):
    """命中人工映射时直接返回（含城市坐标），跳过在线查询。"""
    nets = _load_overrides()
    if not nets:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    for net, city in nets:
        if addr in net:
            if "-" in city:
                prov, cname = city.split("-", 1)
            else:
                prov, cname = "", city
            lat, lon = get_city_coord(cname, prov)
            return {"city": city, "lat": lat, "lon": lon}
    return None


def ip_to_city(ip: str) -> dict:
    """查询 IP 归属地：人工映射优先 → 多源并发交叉校验 → 城市坐标表补经纬度。"""
    # 人工映射（企业固定出口等）优先级最高，命中即返回
    manual = _manual_lookup(ip)
    if manual:
        return manual

    now = time.time()

    cached = _cache.get(ip)
    if cached:
        ttl = _SUCCESS_TTL if cached.get("city") != "未知" else _FAILURE_TTL
        if now - cached.get("_time", 0) < ttl:
            return cached

    geo = _resolve(ip)
    if geo:
        province, city = geo
        label = city if (not province or province == city) else f"{province}-{city}"
        lat, lon = get_city_coord(city, province)
        result = {"city": label, "lat": lat, "lon": lon, "_time": now}
    else:
        result = {"city": "未知", "lat": None, "lon": None, "_time": now}

    _cache[ip] = result

    # 缓存上限：超出 10000 条时，清理 1 小时前的旧项
    if len(_cache) > 10000:
        _cache_new = {k: v for k, v in _cache.items()
                      if isinstance(v, dict) and now - v.get("_time", 0) < 3600}
        _cache.clear()
        _cache.update(_cache_new)

    return result
