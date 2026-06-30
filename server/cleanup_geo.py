"""
一次性脚本：用新的 cip.cc 数据源，把历史 IP 记录的归属地重新查一遍并修正。

用途：切换数据源后，旧记录里的 city/latitude/longitude 是旧源（ip-api.com）给出的
错误值，本脚本逐个 IP 重新查询并更新，让历史数据也变准。

运行方式（在服务器上，cd 到含 ip_tracker.db 的目录，即服务的工作目录）：
    cd /opt/ip-tracker
    python3 cleanup_geo.py

注意：
- 只更新 city/latitude/longitude 三个字段，不删除任何记录（历史轨迹保留）。
- 对同一个 IP 只查一次（ip_to_city 内部有缓存）。
- 每个 IP 之间停 0.4 秒，对 cip.cc 友好一点；查不到的 IP 会跳过、不覆盖原值。
- 想直接清空所有历史记录（重新累积）的话，用命令行：
    sqlite3 ip_tracker.db "DELETE FROM ip_records;"
"""
import os
import sys
import time

# 确保以脚本所在目录为工作目录时，能 import 到 database/models/services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from database import SessionLocal
    from models import IpRecord
    from services.ip_location import ip_to_city

    db = SessionLocal()
    try:
        ips = [row[0] for row in db.query(IpRecord.ip).distinct().all()]
        print(f"共 {len(ips)} 个不同 IP 需要重新归属")
        ok = 0
        fail = 0
        for i, ip in enumerate(ips, 1):
            loc = ip_to_city(ip)
            if loc.get("city") and loc["city"] != "未知":
                db.query(IpRecord).filter(IpRecord.ip == ip).update({
                    "city": loc["city"],
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lon"),
                })
                db.commit()
                ok += 1
                print(f"[{i}/{len(ips)}] {ip} -> {loc['city']}")
                time.sleep(1.2)    # 对 cip.cc 友好，避免触发限流
            else:
                fail += 1
                print(f"[{i}/{len(ips)}] {ip} -> 查询失败/被限流，跳过（保留原值）")
                time.sleep(4)      # cip.cc 可能限流，多等一会再继续
        print(f"\n完成：成功修正 {ok}，失败 {fail}")
        if fail:
            print("提示：失败的多数是 cip.cc 限流，过几分钟重跑一次本脚本即可补上（新进程会重新查询所有 IP）。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
