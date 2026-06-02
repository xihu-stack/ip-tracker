from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    records: Mapped[list["IpRecord"]] = relationship("IpRecord", back_populates="employee", order_by="IpRecord.reported_at.desc()")


class IpRecord(Base):
    __tablename__ = "ip_records"
    __table_args__ = (
        Index("ix_ip_records_employee_reported", "employee_id", "reported_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    city: Mapped[str] = mapped_column(String(128), default="")
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="records")
