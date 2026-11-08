
import logging
import threading

from datetime import datetime
from collections import defaultdict

from scapy.all import sniff, IP, IPv6, TCP, UDP

from app.database import SessionLocal
from app.models import Device, NetworkEvent, Alert

from app.services.risk_analyzer import (
    calculate_indicators,
    get_severity,
)

from app.services.fuzzy_engine import analyze_risk


logger = logging.getLogger(__name__)


# =====================================================
# 1. CONFIGURACAO DO MONITORAMENTO
# =====================================================

# Interface Wi-Fi identificada pelo Scapy/Npcap.
NETWORK_INTERFACE = (
    r"\Device\NPF_{C3C8B96D-E0D2-4D87-A5BE-D50C31B6B803}"
)

# Tempo de cada janela de coleta.
COLLECTION_INTERVAL = 10


# =====================================================
# 2. CLASSE PRINCIPAL DO MONITORAMENTO
# =====================================================

class ContinuousMonitor:

    def __init__(self):

        self.interface = NETWORK_INTERFACE

        self.stop_event = threading.Event()

        self.thread = None

        self.status = "stopped"

        self.lock = threading.Lock()

        self.device_stats = defaultdict(
            self._new_device_stats
        )

    # =================================================
    # 3. ESTRUTURA DAS ESTATISTICAS
    # =================================================

    def _new_device_stats(self):

        return {
            "packet_count": 0,
            "bytes_transferred": 0,
            "destination_ports": set(),
            "protocols": defaultdict(int),
            "last_seen": None,
        }

    # =================================================
    # 4. INICIAR MONITORAMENTO
    # =================================================

    def start(self):

        if self.thread and self.thread.is_alive():

            logger.info(
                "Monitoramento continuo ja esta ativo."
            )

            return

        self.stop_event.clear()

        self.status = "running"

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="SentinelHomeNetworkMonitor",
        )

        self.thread.start()

        logger.info(
            "Monitoramento continuo iniciado."
        )

    # =================================================
    # 5. PARAR MONITORAMENTO
    # =================================================

    def stop(self):

        self.stop_event.set()

        if self.thread and self.thread.is_alive():

            self.thread.join(timeout=12)

        if not self.thread or not self.thread.is_alive():
            self.status = "stopped"

        logger.info(
            "Solicitacao de parada do monitoramento enviada."
        )

    # =================================================
    # 6. CAPTURA E IDENTIFICACAO DOS PACOTES
    # =================================================

    def _capture_packet(self, packet):

        try:

            if IP in packet:

                source_ip = packet[IP].src

            elif IPv6 in packet:

                source_ip = packet[IPv6].src

            else:

                return

            protocol = "OTHER"

            destination_port = None

            if TCP in packet:

                protocol = "TCP"

                destination_port = packet[TCP].dport

            elif UDP in packet:

                protocol = "UDP"

                destination_port = packet[UDP].dport

            packet_size = len(packet)

            with self.lock:

                stats = self.device_stats[source_ip]

                stats["packet_count"] += 1

                stats["bytes_transferred"] += packet_size

                stats["last_seen"] = datetime.utcnow()

                stats["protocols"][protocol] += 1

                if destination_port is not None:

                    stats["destination_ports"].add(
                        destination_port
                    )

        except Exception:

            logger.exception(
                "Erro ao processar pacote capturado."
            )

    # =================================================
    # 7. PROCESSAMENTO DA JANELA DE COLETA
    # =================================================

    def _collect_window(self):

        with self.lock:

            collected_stats = dict(self.device_stats)

            self.device_stats = defaultdict(
                self._new_device_stats
            )

        if not collected_stats:

            logger.info(
                "Nenhum pacote IP coletado nesta janela."
            )

            return

        db = SessionLocal()

        try:

            for source_ip, stats in collected_stats.items():

                # -------------------------------------
                # Localizar dispositivo cadastrado
                # -------------------------------------

                device = (
                    db.query(Device)
                    .filter(
                        Device.ip_address == source_ip
                    )
                    .first()
                )

                if device is None:

                    continue

                # -------------------------------------
                # Preparar dados para normalizacao
                # -------------------------------------

                device_data = {

                    "packet_count": stats["packet_count"],

                    "bytes_transferred": stats["bytes_transferred"],

                    "distinct_destination_ports": len(
                        stats["destination_ports"]
                    ),

                }

                # -------------------------------------
                # Calcular indicadores
                # -------------------------------------

                indicators = calculate_indicators(
                    device_data
                )

                # -------------------------------------
                # Executar motor Fuzzy
                # -------------------------------------

                fuzzy_result = analyze_risk(

                    packet_score=indicators["packet_score"],

                    port_score=indicators["port_score"],

                    traffic_score=indicators["traffic_score"],

                )

                risk_score = float(
                    fuzzy_result["risk_score"]
                )

                classification = fuzzy_result.get(
                    "classification",
                    get_severity(risk_score)
                )

                severity = get_severity(risk_score)

                # -------------------------------------
                # Atualizar risco operacional
                # -------------------------------------

                device.risk_score = risk_score

                device.risk_updated_at = datetime.utcnow()

                device.risk_source = "continuous_monitor"

                # -------------------------------------
                # Criar evento de rede
                # -------------------------------------

                network_event = NetworkEvent(

                    source_ip=source_ip,

                    destination_ip=None,

                    protocol="MULTIPROTOCOLO",

                    event_type="continuous_network_monitoring",

                    packet_count=stats["packet_count"],

                    destination_port=None,

                    bytes_transferred=stats["bytes_transferred"],

                    connection_count=0,

                    severity=severity,

                    risk_score=risk_score,

                    description=(
                        f"Monitoramento continuo. "
                        f"Dispositivo: {device.name}. "
                        f"IP: {source_ip}. "
                        f"Pacotes: {stats['packet_count']}. "
                        f"Bytes: {stats['bytes_transferred']}. "
                        f"Portas distintas: "
                        f"{len(stats['destination_ports'])}. "
                        f"Indicadores Fuzzy: {indicators}. "
                        f"Classificacao: {classification}."
                    ),

                    device_id=device.id,

                )

                db.add(network_event)

                # -------------------------------------
                # Verificar risco critico
                # -------------------------------------

                if risk_score >= 70:

                    existing_alert = (
                        db.query(Alert)
                        .filter(
                            Alert.device_id == device.id,
                            Alert.status == "aberto",
                            Alert.event_type == "continuous_fuzzy_risk",
                        )
                        .first()
                    )

                    # Evitar duplicidade de alertas abertos
                    if not existing_alert:

                        alert = Alert(

                            title=(
                                f"Risco critico detectado: "
                                f"{device.name}"
                            ),

                            description=(
                                f"O monitoramento continuo "
                                f"identificou risco de "
                                f"{risk_score:.2f} no dispositivo "
                                f"{device.name}, IP {source_ip}. "
                                f"O resultado exige investigacao "
                                f"e nao confirma isoladamente "
                                f"um comprometimento."
                            ),

                            event_type="continuous_fuzzy_risk",

                            severity="critico",

                            source_ip=source_ip,

                            risk_score=risk_score,

                            status="aberto",

                            device_id=device.id,

                        )

                        db.add(alert)

                # -------------------------------------
                # Registrar resultado no log
                # -------------------------------------

                logger.info(

                    "Dispositivo: %s | IP: %s | "
                    "Risco: %.2f | Classificacao: %s",

                    device.name,

                    source_ip,

                    risk_score,

                    classification,

                )

            # -----------------------------------------
            # Salvar alteracoes no banco
            # -----------------------------------------

            db.commit()

            logger.info(
                "Janela de monitoramento salva com sucesso."
            )

        except Exception:

            db.rollback()

            logger.exception(
                "Erro ao salvar dados do monitoramento."
            )

        finally:

            db.close()

    # =================================================
    # 8. EXECUCAO DA CAPTURA CONTINUA
    # =================================================

    def _run(self):

        try:

            logger.info(
                "Captura iniciada na interface: %s",
                self.interface,
            )

            while not self.stop_event.is_set():

                packets = sniff(

                    iface=self.interface,

                    timeout=COLLECTION_INTERVAL,

                    store=True,

                )

                for packet in packets:

                    self._capture_packet(packet)

                if self.stop_event.is_set():

                    break

                self._collect_window()

        except Exception:

            self.status = "error"

            logger.exception(
                "Falha no monitoramento continuo."
            )

        finally:

            if self.status != "error":

                self.status = "stopped"

            logger.info(
                "Monitoramento continuo finalizado."
            )


# =====================================================
# 9. INSTANCIA UNICA DA APLICACAO
# =====================================================

monitor = ContinuousMonitor()
