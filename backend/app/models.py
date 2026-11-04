
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Index
)

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), unique=True, nullable=False)
    mac_address = Column(String(17), nullable=True)
    device_type = Column(String(50), default="Desconhecido")
    status = Column(String(20), default="desconhecido")
    risk_score = Column(Float, default=0.0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(80), nullable=False)
    severity = Column(String(20), default="baixo")
    source_ip = Column(String(45), nullable=True)
    risk_score = Column(Float, default=0.0)
    status = Column(String(20), default="aberto")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


Index("idx_alerts_severity", Alert.severity)
Index("idx_alerts_status", Alert.status)
Index("idx_devices_status", Device.status)
