
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertCreate, AlertResponse, AlertStatusUpdate

router = APIRouter(prefix="/api/alerts", tags=["Alertas"])

VALID_SEVERITIES = {"baixo", "moderado", "alto", "critico"}
VALID_STATUSES = {"aberto", "investigando", "resolvido"}


@router.post("/", response_model=AlertResponse, status_code=201)
def create_alert(data: AlertCreate, db: Session = Depends(get_db)):
    if data.severity not in VALID_SEVERITIES:
        raise HTTPException(422, "Gravidade invalida.")

    alert = Alert(**data.model_dump(), status="aberto")

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(422, "Status invalido.")
        query = query.filter(Alert.status == status)

    if severity:
        if severity not in VALID_SEVERITIES:
            raise HTTPException(422, "Gravidade invalida.")
        query = query.filter(Alert.severity == severity)

    return query.order_by(Alert.created_at.desc()).all()


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    data: AlertStatusUpdate,
    db: Session = Depends(get_db)
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(422, "Status invalido.")

    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(404, "Alerta nao encontrado.")

    alert.status = data.status

    if data.status == "resolvido":
        alert.resolved_at = datetime.utcnow()
    else:
        alert.resolved_at = None

    db.commit()
    db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(404, "Alerta nao encontrado.")

    db.delete(alert)
    db.commit()
