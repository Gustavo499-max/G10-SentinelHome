
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


# =====================================================
# DEVICE - DISPOSITIVOS DA REDE
# =====================================================

class Device(Base):
    __tablename__ = "devices"

    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_devices_risk_score",
        ),
        Index("idx_devices_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    mac_address = Column(String(17), nullable=True)
    device_type = Column(String(50), default="Desconhecido", nullable=False)
    status = Column(String(20), default="desconhecido", nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    alerts = relationship(
        "Alert",
        back_populates="device",
        passive_deletes=True,
    )

    network_events = relationship(
        "NetworkEvent",
        back_populates="device",
        passive_deletes=True,
    )


# =====================================================
# ALERT - ALERTAS E INCIDENTES
# =====================================================

class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_alerts_risk_score",
        ),
        Index("idx_alerts_severity", "severity"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(80), nullable=False)
    severity = Column(String(20), default="baixo", nullable=False)
    source_ip = Column(String(45), nullable=True)
    risk_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="aberto", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    device = relationship(
        "Device",
        back_populates="alerts",
    )


# =====================================================
# NETWORK EVENT - EVENTOS DE REDE
# =====================================================

class NetworkEvent(Base):
    __tablename__ = "network_events"

    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_network_events_risk_score",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_network_events_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_network_events_longitude",
        ),
        CheckConstraint(
            "packet_count IS NULL OR packet_count >= 0",
            name="ck_network_events_packet_count",
        ),
        CheckConstraint(
            "destination_port IS NULL OR (destination_port >= 1 AND destination_port <= 65535)",
            name="ck_network_events_destination_port",
        ),
        CheckConstraint(
            "bytes_transferred IS NULL OR bytes_transferred >= 0",
            name="ck_network_events_bytes",
        ),
        CheckConstraint(
            "connection_count IS NULL OR connection_count >= 0",
            name="ck_network_events_connections",
        ),
        Index("idx_network_events_source_ip", "source_ip"),
        Index("idx_network_events_destination_ip", "destination_ip"),
        Index("idx_network_events_severity", "severity"),
        Index("idx_network_events_created_at", "created_at"),
        Index("idx_network_events_device_id", "device_id"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Endereços IP
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)

    # Protocolo de rede
    protocol = Column(String(20), nullable=True)

    # Tipo de evento
    event_type = Column(String(100), nullable=False)

    # Indicadores de telemetria
    packet_count = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    bytes_transferred = Column(Integer, nullable=True)
    connection_count = Column(Integer, nullable=True)

    # Classificação e risco
    severity = Column(String(20), default="baixo", nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)

    # Geolocalização aproximada de IP público
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country = Column(String(100), nullable=True)

    # Evidências
    description = Column(Text, nullable=True)

    # Dispositivo associado
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    device = relationship(
        "Device",
        back_populates="network_events",
    )
