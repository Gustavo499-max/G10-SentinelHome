
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Device, Alert

router = APIRouter(prefix="/api/analytics", tags=["Indicadores"])


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

    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices
        },
        "alerts": {
            "total": total_alerts,
            "open": open_alerts,
            "critical": critical_alerts
        },
        "average_device_risk": round(average_risk or 0, 2)
    }


@router.get("/severity")
def alerts_by_severity(db: Session = Depends(get_db)):
    results = (
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )

    return {
        item[0]: item[1]
        for item in results
    }


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
        {"date": str(date), "count": count}
        for date, count in results
    ]
