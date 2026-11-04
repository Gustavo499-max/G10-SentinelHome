
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device
from app.schemas import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["Dispositivos"])


@router.post("/", response_model=DeviceResponse, status_code=201)
def create_device(data: DeviceCreate, db: Session = Depends(get_db)):
    ip = str(data.ip_address)

    existing = db.query(Device).filter(
        Device.ip_address == ip
    ).first()

    if existing:
        raise HTTPException(409, "IP ja cadastrado.")

    device = Device(
        name=data.name,
        ip_address=ip,
        mac_address=data.mac_address,
        device_type=data.device_type,
        status="online",
        last_seen=datetime.utcnow()
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.get("/", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.id.desc()).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(404, "Dispositivo nao encontrado.")

    return device


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(404, "Dispositivo nao encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    return device


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(404, "Dispositivo nao encontrado.")

    db.delete(device)
    db.commit()
