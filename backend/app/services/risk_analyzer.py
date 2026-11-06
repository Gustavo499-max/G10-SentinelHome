
from sqlalchemy.orm import Session

from app.models import Device, NetworkEvent, Alert
from app.services.network_monitor import analyze_pcap
from app.services.fuzzy_engine import analyze_risk


# =====================================================
# 1. CONFIGURACAO DOS INDICADORES
# =====================================================

# Limites iniciais para normalizar os dados entre 0 e 100.
# Sao parametros heurísticos, nao limites universais de ataque.
# Posteriormente serao calibrados com capturas reais.

PACKETS_REFERENCE = 1000
PORTS_REFERENCE = 20
TRAFFIC_REFERENCE = 1_000_000  # 1 MB


# =====================================================
# 2. NORMALIZACAO DOS INDICADORES
# =====================================================

def normalize_score(value: int, reference: int) -> float:
    """
    Converte uma quantidade em um indicador de 0 a 100.
    """

    if reference <= 0:
        raise ValueError("A referencia deve ser maior que zero.")

    score = (value / reference) * 100

    return round(min(max(score, 0), 100), 2)


def calculate_indicators(device_data: dict) -> dict:
    """
    Calcula os indicadores que serao enviados ao motor Fuzzy.
    """

    packet_count = device_data["packet_count"]

    distinct_ports = device_data["distinct_destination_ports"]

    bytes_transferred = device_data["bytes_transferred"]

    return {
        "packet_score": normalize_score(
            packet_count,
            PACKETS_REFERENCE,
        ),

        "port_score": normalize_score(
            distinct_ports,
            PORTS_REFERENCE,
        ),

        "traffic_score": normalize_score(
            bytes_transferred,
            TRAFFIC_REFERENCE,
        ),
    }


# =====================================================
# 3. CLASSIFICACAO DA SEVERIDADE
# =====================================================

def get_severity(risk_score: float) -> str:
    """
    Converte o indice Fuzzy em uma severidade.
    """

    if risk_score >= 70:
        return "critico"

    if risk_score >= 40:
        return "moderado"

    return "baixo"


# =====================================================
# 4. ANALISE DA CAPTURA E VINCULACAO AOS DISPOSITIVOS
# =====================================================

def analyze_capture_for_devices(
    db: Session,
    file_path: str,
) -> dict:
    """
    Analisa um PCAP/PCAPNG e associa os dados aos
    dispositivos cadastrados pelo IP de origem.

    Cada dispositivo correspondente recebe um
    NetworkEvent agregado por captura.
    """

    try:

        # ---------------------------------------------
        # Analise da captura
        # ---------------------------------------------

        capture = analyze_pcap(file_path)

        analyzed_devices = []
        unmatched_ips = []

        # ---------------------------------------------
        # Processamento individual dos dispositivos
        # ---------------------------------------------

        for device_data in capture["device_stats"]:

            source_ip = device_data["ip"]

            device = (
                db.query(Device)
                .filter(Device.ip_address == source_ip)
                .first()
            )

            # IP nao cadastrado
            if device is None:

                unmatched_ips.append(source_ip)

                continue

            # -----------------------------------------
            # Calculo dos indicadores
            # -----------------------------------------

            indicators = calculate_indicators(device_data)

            # -----------------------------------------
            # Execucao do motor Fuzzy
            # -----------------------------------------

            fuzzy_result = analyze_risk(
                packet_score=indicators["packet_score"],
                port_score=indicators["port_score"],
                traffic_score=indicators["traffic_score"],
            )

            risk_score = fuzzy_result["risk_score"]

            classification = fuzzy_result["classification"]

            severity = get_severity(risk_score)

            # -----------------------------------------
            # Evidencias do dispositivo
            # -----------------------------------------

            ports = device_data["destination_ports"]

            port_list = [
                item["port"]
                for item in ports
            ]

            description = (
                f"Analise de captura PCAP/PCAPNG. "
                f"Dispositivo: {device.name}. "
                f"IP: {source_ip}. "
                f"Pacotes: {device_data['packet_count']}. "
                f"Bytes: {device_data['bytes_transferred']}. "
                f"Fluxos distintos: {device_data['connection_count']}. "
                f"Portas distintas: "
                f"{device_data['distinct_destination_ports']}. "
                f"Portas observadas: {port_list}. "
                f"Indicadores Fuzzy: {indicators}. "
                f"Classificacao: {classification}."
            )

            # -----------------------------------------
            # Registro do evento
            # -----------------------------------------

            network_event = NetworkEvent(
                source_ip=source_ip,
                destination_ip=None,
                protocol="MULTIPROTOCOLO",
                event_type="pcap_device_analysis",
                packet_count=device_data["packet_count"],
                destination_port=None,
                bytes_transferred=device_data["bytes_transferred"],
                connection_count=device_data["connection_count"],
                severity=severity,
                risk_score=risk_score,
                description=description,
                device_id=device.id,
            )

            db.add(network_event)

            # -----------------------------------------
            # Atualizacao do dispositivo
            # -----------------------------------------

            device.risk_score = risk_score

            # -----------------------------------------
            # Criacao de alerta critico
            # -----------------------------------------

            if risk_score >= 70:

                alert = Alert(
                    title=f"Risco critico detectado: {device.name}",
                    description=(
                        f"O motor Fuzzy identificou um indice de risco "
                        f"de {risk_score} durante a analise da captura. "
                        f"Este resultado exige investigacao e nao "
                        f"confirma, isoladamente, um comprometimento."
                    ),
                    event_type="fuzzy_risk_analysis",
                    severity="critico",
                    source_ip=source_ip,
                    risk_score=risk_score,
                    status="aberto",
                    device_id=device.id,
                )

                db.add(alert)

            # -----------------------------------------
            # Resultado individual
            # -----------------------------------------

            analyzed_devices.append({
                "device_id": device.id,
                "device_name": device.name,
                "ip_address": source_ip,
                "risk_score": risk_score,
                "classification": classification,
                "severity": severity,
                "indicators": indicators,
                "packet_count": device_data["packet_count"],
                "bytes_transferred": device_data["bytes_transferred"],
                "connection_count": device_data["connection_count"],
                "distinct_destination_ports": (
                    device_data["distinct_destination_ports"]
                ),
            })

        # ---------------------------------------------
        # Persistencia no banco
        # ---------------------------------------------

        db.commit()

        return {
            "success": True,
            "capture": {
                "total_packets": capture["total_packets"],
                "total_bytes": capture["total_bytes"],
            },
            "devices_analyzed": len(analyzed_devices),
            "devices": analyzed_devices,
            "unmatched_ips": unmatched_ips,
        }

    except Exception:
        db.rollback()
        raise
