
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import (
    AlertCreate,
    AlertResponse,
    AlertStatusUpdate,
)


# =====================================================
# CONFIGURACAO DA ROTA
# =====================================================

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alertas"],
)


# =====================================================
# REGRAS DE VALIDACAO
# =====================================================

VALID_SEVERITIES = {
    "baixo",
    "moderado",
    "alto",
    "critico",
}

VALID_STATUSES = {
    "aberto",
    "investigando",
    "resolvido",
}


# =====================================================
# FUNCAO AUXILIAR — BUSCAR ALERTA
# =====================================================

def find_alert(db: Session, alert_id: int):

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta nao encontrado.",
        )

    return alert


# =====================================================
# CRIAR ALERTA
# =====================================================

@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(
    data: AlertCreate,
    db: Session = Depends(get_db),
):
    """
    Registra um novo alerta de seguranca.
    """

    severity = data.severity.strip().lower()

    if severity not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gravidade invalida.",
        )

    alert_data = data.model_dump()

    alert_data["severity"] = severity

    alert = Alert(
        **alert_data,
        status="aberto",
    )

    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar o alerta.",
        )


# =====================================================
# LISTAR ALERTAS
# =====================================================

@router.get(
    "/",
    response_model=list[AlertResponse],
)
def list_alerts(
    status_filter: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Lista alertas com filtros opcionais.
    """

    query = db.query(Alert)

    if status_filter:

        status_filter = status_filter.strip().lower()

        if status_filter not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status invalido.",
            )

        query = query.filter(
            Alert.status == status_filter
        )

    if severity:

        severity = severity.strip().lower()

        if severity not in VALID_SEVERITIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Gravidade invalida.",
            )

        query = query.filter(
            Alert.severity == severity
        )

    return (
        query
        .order_by(Alert.created_at.desc())
        .all()
    )


# =====================================================
# ATUALIZAR STATUS DO ALERTA
# =====================================================

@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
)
def update_alert(
    alert_id: int,
    data: AlertStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza o status de um alerta.
    """

    new_status = data.status.strip().lower()

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status invalido.",
        )

    alert = find_alert(db, alert_id)

    alert.status = new_status

    if new_status == "resolvido":
        alert.resolved_at = datetime.utcnow()
    else:
        alert.resolved_at = None

    try:
        db.commit()
        db.refresh(alert)

        return alert

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar o alerta.",
        )


# =====================================================
# EXCLUIR ALERTA
# =====================================================

@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """
    Exclui um alerta do sistema.
    """

    alert = find_alert(db, alert_id)

    try:
        db.delete(alert)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao excluir o alerta.",
        )
