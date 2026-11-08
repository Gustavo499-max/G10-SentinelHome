from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, NetworkEvent
from app.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
)
from app.services.fuzzy_engine import (
    analyze_risk,
    classify_risk,
)


# =====================================================
# 1. CONFIGURACAO DA ROTA
# =====================================================

router = APIRouter(
    prefix="/api/devices",
    tags=["Dispositivos"],
)


# =====================================================
# 2. MODELO DE ENTRADA PARA O CALCULO FUZZY
# =====================================================

class FuzzyRiskRequest(BaseModel):

    packet_score: float = Field(
        ge=0,
        le=100,
        description="Indicador de pacotes entre 0 e 100.",
    )

    port_score: float = Field(
        ge=0,
        le=100,
        description="Indicador de portas entre 0 e 100.",
    )

    traffic_score: float = Field(
        ge=0,
        le=100,
        description="Indicador de trafego entre 0 e 100.",
    )


class DiscoveredDeviceRequest(BaseModel):
    ip_address: str = Field(min_length=7, max_length=45)
    mac_address: str = Field(min_length=17, max_length=17)
    device_type: str = Field(
        default="Desconhecido",
        max_length=50,
    )


# =====================================================
# 3. FUNCAO AUXILIAR - BUSCAR DISPOSITIVO
# =====================================================

def find_device(db: Session, device_id: int):

    device = (
        db.query(Device)
        .filter(Device.id == device_id)
        .first()
    )

    if not device:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo nao encontrado.",
        )

    return device


# =====================================================
# 4. CADASTRAR DISPOSITIVO
# =====================================================

@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
):
    """
    Cadastra um dispositivo manualmente no inventario.
    """

    ip = str(data.ip_address)

    existing = (
        db.query(Device)
        .filter(Device.ip_address == ip)
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este endereco IP ja esta cadastrado.",
        )

    device = Device(
        name=data.name.strip(),
        ip_address=ip,
        mac_address=data.mac_address,
        device_type=data.device_type,
        status="desconhecido",
        risk_score=0.0,
        last_seen=None,
    )

    try:

        db.add(device)
        db.commit()
        db.refresh(device)

        return device

    except IntegrityError as error:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao foi possivel cadastrar: IP ou registro duplicado.",
        ) from error

    except Exception:

        db.rollback()
        raise


# =====================================================
# 5. LISTAR DISPOSITIVOS
# =====================================================
# =====================================================
# CADASTRO INTELIGENTE DE DISPOSITIVOS DESCOBERTOS
# =====================================================

@router.post("/register-discovered")
def register_discovered_devices(
    data: list[DiscoveredDeviceRequest],
    db: Session = Depends(get_db),
):
    """
    Cadastra dispositivos identificados pela descoberta ARP.

    Evita duplicidade de IP e endereço MAC.
    """

    import ipaddress
    from sqlalchemy import func

    created_devices = []
    skipped_devices = []

    try:
        for item in data:

            ip = str(ipaddress.ip_address(item.ip_address))
            mac = item.mac_address.strip().lower()

            # Verifica formato básico do MAC
            import re

            if not re.fullmatch(
                r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}",
                mac
            ):
                skipped_devices.append({
                    "ip_address": ip,
                    "reason": "Endereço MAC inválido."
                })
                continue

            # Verifica IP duplicado
            existing_ip = (
                db.query(Device)
                .filter(Device.ip_address == ip)
                .first()
            )

            if existing_ip:
                skipped_devices.append({
                    "ip_address": ip,
                    "reason": "IP já cadastrado."
                })
                continue

            # Verifica MAC duplicado
            existing_mac = (
                db.query(Device)
                .filter(
                    func.lower(Device.mac_address) == mac
                )
                .first()
            )

            if existing_mac:
                skipped_devices.append({
                    "ip_address": ip,
                    "reason": "MAC já cadastrado em outro dispositivo."
                })
                continue

            device = Device(
                name=f"Dispositivo {ip}",
                ip_address=ip,
                mac_address=mac,
                device_type=item.device_type.strip(),
                status="online",
                risk_score=0.0,
                last_seen=datetime.utcnow(),
            )

            db.add(device)
            db.flush()

            created_devices.append({
                "id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "device_type": device.device_type,
                "status": device.status,
            })

        db.commit()

        return {
            "success": True,
            "message": "Processamento dos dispositivos concluído.",
            "total_received": len(data),
            "total_created": len(created_devices),
            "total_skipped": len(skipped_devices),
            "created_devices": created_devices,
            "skipped_devices": skipped_devices,
        }

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=f"Endereço IP inválido: {error}",
        ) from error

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Conflito ao cadastrar dispositivos. Verifique IPs e MACs duplicados.",
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar dispositivos descobertos.",
        ) from error
    
@router.get(
    "/",
    response_model=list[DeviceResponse],
)
def list_devices(
    db: Session = Depends(get_db),
):
    """
    Retorna todos os dispositivos cadastrados.
    """

    return (
        db.query(Device)
        .order_by(Device.id.desc())
        .all()
    )


# =====================================================
# 6. CONSULTAR DISPOSITIVO POR ID
# =====================================================

@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna os detalhes de um dispositivo.
    """

    return find_device(db, device_id)



@router.post("/{device_id}/calculate-risk")
def calculate_device_risk(
    device_id: int,
    data: FuzzyRiskRequest,
    db: Session = Depends(get_db),
):
    """
    Executa uma simulacao Fuzzy experimental.

    O resultado e registrado como evento experimental,
    sem alterar o risco operacional do dispositivo.
    """

    device = find_device(db, device_id)

    try:
        # 1. EXECUCAO DO MOTOR FUZZY
        result = analyze_risk(
            packet_score=data.packet_score,
            port_score=data.port_score,
            traffic_score=data.traffic_score,
        )

        risk_score = result["risk_score"]
        classification = result["classification"]

        # 2. REGISTRO SEPARADO DA SIMULACAO
        event = NetworkEvent(
            source_ip=device.ip_address,
            event_type="experimental_fuzzy_assessment",
            severity=classification,
            risk_score=risk_score,
            description=(
                "SIMULACAO FUZZY EXPERIMENTAL. "
                "Este resultado nao representa telemetria real "
                "e nao altera o risco operacional do dispositivo. "
                f"Pacotes: {data.packet_score}; "
                f"Portas: {data.port_score}; "
                f"Trafego: {data.traffic_score}; "
                f"Classificacao: {classification}; "
                f"Indice de risco: {risk_score}."
            ),
            device_id=device.id,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        # 3. RESPOSTA DA API
        return {
            "success": True,
            "message": "Simulacao Fuzzy concluida e registrada.",
            "experimental": True,
            "operational_risk_updated": False,

            "device": {
                "id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "device_type": device.device_type,
            },

            "risk": {
                "score": risk_score,
                "classification": classification,
            },

            "indicators": result["indicators"],

            "event": {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "created_at": event.created_at.isoformat(),
            },

            "operational_risk": {
                "score": round(float(device.risk_score or 0.0), 2),
                "updated_at": (
                    device.risk_updated_at.isoformat()
                    if device.risk_updated_at
                    else None
                ),
                "source": device.risk_source,
            },
        }

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao calcular e registrar a simulacao Fuzzy.",
        ) from error

# =====================================================
# 8. CONSULTAR RISCO E HISTORICO DO DISPOSITIVO
# =====================================================

@router.get("/{device_id}/risk")
def get_device_risk(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna o risco persistido e os eventos recentes
    associados ao dispositivo.
    """

    device = find_device(db, device_id)

    events = (
        db.query(NetworkEvent)
        .filter(NetworkEvent.device_id == device.id)
        .order_by(NetworkEvent.created_at.desc())
        .limit(20)
        .all()
    )

    total_events = (
        db.query(NetworkEvent)
        .filter(NetworkEvent.device_id == device.id)
        .count()
    )

    risk_score = float(device.risk_score or 0.0)

    return {
        "device": {
            "id": device.id,
            "name": device.name,
            "ip_address": device.ip_address,
            "status": device.status,
        },

        "risk": {
            "score": round(risk_score, 2),
            "classification": classify_risk(risk_score),
        },

        "events": {
            "total": total_events,

            "recent": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "risk_score": event.risk_score,
                    "packet_count": event.packet_count,
                    "destination_port": event.destination_port,
                    "bytes_transferred": event.bytes_transferred,
                    "connection_count": event.connection_count,
                    "created_at": event.created_at.isoformat(),
                }

                for event in events
            ],
        },
    }


# =====================================================
# 9. ATUALIZAR DISPOSITIVO
# =====================================================

@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza as informacoes de um dispositivo.
    """

    device = find_device(db, device_id)

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():

        if isinstance(value, str):
            value = value.strip()

        setattr(device, field, value)

    try:

        db.commit()
        db.refresh(device)

        return device

    except IntegrityError as error:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao foi possivel atualizar o dispositivo.",
        ) from error

    except Exception:

        db.rollback()
        raise


# =====================================================
# 10. EXCLUIR DISPOSITIVO
# =====================================================

@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove um dispositivo do inventario.

    Alertas e eventos associados devem permanecer
    registrados, com device_id definido como NULL.
    """

    device = find_device(db, device_id)

    try:

        db.delete(device)
        db.commit()

    except Exception:

        db.rollback()
        raise
