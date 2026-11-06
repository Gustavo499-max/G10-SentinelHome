
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Device, Alert, NetworkEvent


router = APIRouter(
    prefix="/api/analytics",
    tags=["Indicadores"],
)


# =====================================================
# 1. RESUMO GERAL DO SENTINELHOME
# =====================================================

@router.get("/summary")
def summary(db: Session = Depends(get_db)):

    total_devices = db.query(Device).count()

    online_devices = db.query(Device).filter(
        Device.status == "online"
    ).count()

    total_alerts = db.query(Alert).count()

    open_alerts = db.query(Alert).filter(
        Alert.status == "aberto"
    ).count()

    critical_alerts = db.query(Alert).filter(
        Alert.severity == "critico",
        Alert.status != "resolvido"
    ).count()

    average_risk = db.query(
        func.avg(Device.risk_score)
    ).scalar()

    total_events = db.query(NetworkEvent).count()

    suspicious_events = db.query(NetworkEvent).filter(
        NetworkEvent.severity.in_(["alto", "critico"])
    ).count()

    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices,
        },
        "alerts": {
            "total": total_alerts,
            "open": open_alerts,
            "critical": critical_alerts,
        },
        "network_events": {
            "total": total_events,
            "suspicious": suspicious_events,
        },
        "average_device_risk": round(
            average_risk or 0, 2
        ),
    }


# =====================================================
# 2. DISTRIBUICAO DE ALERTAS POR GRAVIDADE
# =====================================================

@router.get("/severity")
def alerts_by_severity(db: Session = Depends(get_db)):

    results = (
        db.query(
            Alert.severity,
            func.count(Alert.id)
        )
        .group_by(Alert.severity)
        .all()
    )

    return {
        item[0]: item[1]
        for item in results
    }


# =====================================================
# 3. HISTORICO DE ALERTAS
# =====================================================

@router.get("/timeline")
def alert_timeline(db: Session = Depends(get_db)):

    results = (
        db.query(
            func.date(Alert.created_at),
            func.count(Alert.id)
        )
        .group_by(func.date(Alert.created_at))
        .order_by(func.date(Alert.created_at))
        .all()
    )

    return [
        {
            "date": str(date),
            "count": count,
        }
        for date, count in results
    ]


# =====================================================
# 4. DISTRIBUICAO DE EVENTOS DE REDE
# =====================================================

@router.get("/network-events")
def network_events_summary(db: Session = Depends(get_db)):

    total = db.query(NetworkEvent).count()

    results = (
        db.query(
            NetworkEvent.severity,
            func.count(NetworkEvent.id)
        )
        .group_by(NetworkEvent.severity)
        .all()
    )

    severity_distribution = {
        severity: count
        for severity, count in results
    }

    return {
        "total": total,
        "severity_distribution": severity_distribution,
    }


# =====================================================
# 5. DISTRIBUICAO GEOGRAFICA DOS EVENTOS
# =====================================================

@router.get("/geographic")
def geographic_summary(db: Session = Depends(get_db)):

    results = (
        db.query(
            NetworkEvent.country,
            func.count(NetworkEvent.id)
        )
        .filter(
            NetworkEvent.country.isnot(None),
            NetworkEvent.latitude.isnot(None),
            NetworkEvent.longitude.isnot(None),
        )
        .group_by(NetworkEvent.country)
        .order_by(func.count(NetworkEvent.id).desc())
        .all()
    )

    return [
        {
            "country": country,
            "events": count,
        }
        for country, count in results
    ]


# =====================================================
# 6. INDICADORES DE RISCO DOS DISPOSITIVOS
# =====================================================

@router.get("/device-risks")
def device_risks(db: Session = Depends(get_db)):

    devices = (
        db.query(Device)
        .order_by(Device.risk_score.desc())
        .all()
    )

    return [
        {
            "id": device.id,
            "name": device.name,
            "ip_address": device.ip_address,
            "status": device.status,
            "risk_score": device.risk_score,
        }
        for device in devices
    ]
