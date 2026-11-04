
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    ip_address: IPvAnyAddress
    mac_address: Optional[str] = None
    device_type: str = Field(default="Desconhecido", max_length=50)


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)


class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    mac_address: Optional[str]
    device_type: str
    status: str
    risk_score: float
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: Optional[str] = None
    event_type: str = Field(min_length=2, max_length=80)
    severity: str = "baixo"
    source_ip: Optional[str] = None
    risk_score: float = Field(default=0, ge=0, le=100)


class AlertStatusUpdate(BaseModel):
    status: str


class AlertResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    severity: str
    source_ip: Optional[str]
    risk_score: float
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
