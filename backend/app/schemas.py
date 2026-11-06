
from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
)


# =====================================================
# DEVICE — CADASTRO DE DISPOSITIVOS
# =====================================================

class DeviceCreate(BaseModel):
    """
    Dados utilizados para registrar um dispositivo
    no inventario do SentinelHome.
    """

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    ip_address: IPvAnyAddress

    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
    )

    device_type: str = Field(
        default="Desconhecido",
        max_length=50,
    )


# =====================================================
# DEVICE — ATUALIZACAO
# =====================================================

class DeviceUpdate(BaseModel):
    """
    Campos que podem ser atualizados
    em um dispositivo existente.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
    )

    device_type: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    status: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    risk_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )


# =====================================================
# DEVICE — RESPOSTA DA API
# =====================================================

class DeviceResponse(BaseModel):
    """
    Estrutura devolvida pela API
    ao consultar um dispositivo.
    """

    id: int
    name: str
    ip_address: str
    mac_address: Optional[str] = None
    device_type: str
    status: str
    risk_score: float
    last_seen: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


# =====================================================
# ALERT — CRIACAO DE ALERTAS
# =====================================================

class AlertCreate(BaseModel):
    """
    Dados necessarios para registrar
    um evento de seguranca como alerta.
    """

    title: str = Field(
        min_length=3,
        max_length=150,
    )

    description: Optional[str] = None

    event_type: str = Field(
        min_length=2,
        max_length=80,
    )

    severity: str = Field(
        default="baixo",
        max_length=20,
    )

    source_ip: Optional[str] = None

    risk_score: float = Field(
        default=0,
        ge=0,
        le=100,
    )


# =====================================================
# ALERT — ATUALIZACAO DE STATUS
# =====================================================

class AlertStatusUpdate(BaseModel):

    status: str = Field(
        min_length=3,
        max_length=20,
    )


# =====================================================
# ALERT — RESPOSTA DA API
# =====================================================

class AlertResponse(BaseModel):

    id: int
    title: str
    description: Optional[str] = None
    event_type: str
    severity: str
    source_ip: Optional[str] = None
    risk_score: float
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


# =====================================================
# NETWORK EVENT — REGISTRO DE EVENTOS DE REDE
# =====================================================

class NetworkEventCreate(BaseModel):
    """
    Informacoes de um evento observado na rede.

    Os dados poderao alimentar:
    - Mapa de topologia;
    - Mapa geografico;
    - Motor de risco Fuzzy;
    - Central de alertas.
    """

    source_ip: Optional[str] = Field(
        default=None,
        max_length=45,
    )

    destination_ip: Optional[str] = Field(
        default=None,
        max_length=45,
    )

    protocol: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    event_type: str = Field(
        min_length=2,
        max_length=100,
    )

    severity: str = Field(
        default="baixo",
        max_length=20,
    )

    risk_score: float = Field(
        default=0,
        ge=0,
        le=100,
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
    )

    country: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    description: Optional[str] = None

    device_id: Optional[int] = Field(
        default=None,
        gt=0,
    )


# =====================================================
# NETWORK EVENT — RESPOSTA DA API
# =====================================================

class NetworkEventResponse(BaseModel):
    """
    Estrutura devolvida pela API
    ao consultar um evento de rede.
    """

    id: int
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    protocol: Optional[str] = None
    event_type: str
    severity: str
    risk_score: float

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None

    description: Optional[str] = None
    device_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
