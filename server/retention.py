"""
IP 记录保留期清理：删除超过保留期的历史记录，防止 ip_records 无限膨胀。

保留天数由环境变量 IP_TRACKER_RETENTION_DAYS 控制，默认 365 天（0 = 不清理）。
只删 ip_records，不动 employees（设备台账保留，仅清历史轨迹）。

用法（在服务器上）：
    cd /opt/ip-tracker
    venv/bin/python retention.py                # 按 365 天清理
    IP_TRACKER_RETENTION_DAYS=90 venv/bin/python retention.py

install.sh 会注册每周日 03:00 的 systemd timer 自动执行。
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from database import SessionLocal
    from models import IpRecord

    days = int(os.getenv("IP_TRACKER_RETENTION_DAYS", "365"))
    if days <= 0:
        print("IP_TRACKER_RETENTION_DAYS <= 0，跳过清理")
        return

    cutoff = datetime.now() - timedelta(days=days)
    db = SessionLocal()
    try:
        deleted = db.query(IpRecord).filter(IpRecord.reported_at < cutoff).delete()
        db.commit()
        print(f"保留期 {days} 天：已清理 {deleted} 条 {cutoff.strftime('%Y-%m-%d')} 之前的 IP 记录")
    finally:
        db.close()


if __name__ == "__main__":
    main()
