import urllib.request
import json
import time


_cache = {}


def ip_to_city(ip: str) -> dict:
    """通过 ip-api.com 在线查询 IP 对应城市和经纬度，返回 {city, lat, lon}"""
    if ip in _cache:
        return _cache[ip]

    result = {"city": "未知", "lat": None, "lon": None}

    try:
        url = f"http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,regionName,city,districtName,lat,lon"
        req = urllib.request.Request(url, headers={"User-Agent": "IPTracker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") == "success":
            region = data.get("regionName", "")
            city = data.get("city", "")
            district = data.get("districtName", "")
            parts = [p for p in [region, city, district] if p]
            # 去重相邻重复（如 "上海-上海-浦东" → "上海-浦东"）
            deduped = [parts[0]] + [parts[i] for i in range(1, len(parts)) if parts[i] != parts[i - 1]]
            city_str = "-".join(deduped) if deduped else "未知"
            result = {
                "city": city_str,
                "lat": data.get("lat"),
                "lon": data.get("lon")
            }
    except Exception:
        pass

    result["_time"] = time.time()

    # 缓存所有结果（包括"未知"），避免重复请求外部 API
    _cache[ip] = result
    if len(_cache) > 10000:
        now = time.time()
        _cache_new = {k: v for k, v in _cache.items()
                      if isinstance(v, dict) and v.get("_time") and now - v["_time"] < 3600}
        _cache.clear()
        _cache.update(_cache_new)
    return result
