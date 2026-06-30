import json
import time
import urllib.request

try:
    from .city_coords import get_city_coord
except ImportError:  # 兼容直接以模块方式运行（如一次性脚本）
    from city_coords import get_city_coord


_cache = {}
_SUCCESS_TTL = 3600   # 成功结果缓存 1 小时（同一 IP 期间不再请求外部）
_FAILURE_TTL = 300    # 失败结果只缓存 5 分钟，便于尽快重试

_COUNTRY_TOKENS = {"中国", "China", "china", "PRC"}


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
            text = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        # 网络错误 / 503 限流 / 超时等：交由后续数据源兜底
        return None

    def _parts_of(line_prefix: str):
        for line in text.splitlines():
            if line_prefix in line and ":" in line:
                val = line.split(":", 1)[1].strip()
                return [p for p in val.split() if p and p not in _COUNTRY_TOKENS]
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
    if not province and not city:
        return None
    if not city:
        city = province
    return province, city


def _query_pconline(ip: str):
    """数据源 2：太平洋 pconline，JSON 格式，免 key。返回 (province, city) 或 None。

    返回示例：{"pro":"江苏省","city":"南京市","addr":"江苏省南京市 电信","err":""}
    """
    try:
        url = f"https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true"
        req = urllib.request.Request(url, headers={"User-Agent": "IPTracker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
        data = json.loads(text)
        if data.get("err"):
            return None
        province = (data.get("pro") or "").replace("省", "").replace("市", "")
        city = (data.get("city") or "").replace("市", "")
        if not province and not city:
            return None
        if not city:
            city = province
        return province, city
    except Exception:
        return None


# 数据源顺序：前面的优先；任一被限流/失败时自动尝试后面的。要加更多源，往这里加一个函数即可。
_SOURCES = (_query_cip_cc, _query_pconline)


def _resolve(ip: str):
    """依次尝试多个数据源，第一个成功的结果即返回；全部失败返回 None。"""
    for fn in _SOURCES:
        try:
            geo = fn(ip)
        except Exception:
            geo = None
        if geo:
            return geo
    return None


def ip_to_city(ip: str) -> dict:
    """查询 IP 归属地：多源轮询，再用城市坐标表补经纬度。返回 {city, lat, lon}。"""
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
