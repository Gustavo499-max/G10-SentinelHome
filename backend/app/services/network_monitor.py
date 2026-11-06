
from collections import Counter, defaultdict
from pathlib import Path

from scapy.all import (
    IP,
    IPv6,
    TCP,
    UDP,
    ICMP,
    ARP,
    rdpcap,
)


# =====================================================
# ANALISADOR DE CAPTURAS DE REDE
# =====================================================

def analyze_pcap(file_path: str):
    """
    Analisa arquivos PCAP e PCAPNG.

    Retorna:
    - Total de pacotes e bytes;
    - Protocolos de rede e transporte;
    - Principais IPs de origem e destino;
    - Portas de destino mais utilizadas;
    - Estatísticas individuais por IP de origem;
    - Fluxos distintos de comunicação.
    """

    path = Path(file_path)

    # =================================================
    # 1. VALIDACAO DO ARQUIVO
    # =================================================

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(
            "Arquivo de captura nao encontrado."
        )

    if path.suffix.lower() not in {".pcap", ".pcapng"}:
        raise ValueError(
            "Formato permitido: PCAP ou PCAPNG."
        )

    if path.stat().st_size == 0:
        raise ValueError(
            "O arquivo de captura esta vazio."
        )

    # =================================================
    # 2. LEITURA DA CAPTURA
    # =================================================

    try:
        packets = rdpcap(str(path))

    except Exception as error:
        raise ValueError(
            "Nao foi possivel interpretar o arquivo de captura."
        ) from error

    # =================================================
    # 3. CONTADORES GERAIS
    # =================================================

    source_ips = Counter()
    destination_ips = Counter()
    destination_ports = Counter()

    network_protocols = Counter()
    transport_protocols = Counter()

    total_bytes = 0

    # Estatisticas individuais por IP de origem
    device_stats = defaultdict(
        lambda: {
            "packet_count": 0,
            "bytes_transferred": 0,
            "connection_count": 0,
            "destination_ports": Counter(),
            "protocols": Counter(),
            "flows": set(),
        }
    )

    # =================================================
    # 4. PROCESSAMENTO DOS PACOTES
    # =================================================

    for packet in packets:

        packet_size = len(packet)

        total_bytes += packet_size

        source_ip = None
        destination_ip = None

        # ---------------------------------------------
        # IPv4
        # ---------------------------------------------

        if IP in packet:

            source_ip = packet[IP].src
            destination_ip = packet[IP].dst

            network_protocols["IPv4"] += 1

        # ---------------------------------------------
        # IPv6
        # ---------------------------------------------

        elif IPv6 in packet:

            source_ip = packet[IPv6].src
            destination_ip = packet[IPv6].dst

            network_protocols["IPv6"] += 1

        # ---------------------------------------------
        # ARP
        # ---------------------------------------------

        elif ARP in packet:

            network_protocols["ARP"] += 1

        else:

            network_protocols["OUTROS"] += 1

        # Pacotes sem IP nao entram na estatistica
        # individual por dispositivo.

        if source_ip is None:
            continue

        source_ips[source_ip] += 1
        destination_ips[destination_ip] += 1

        stats = device_stats[source_ip]

        stats["packet_count"] += 1
        stats["bytes_transferred"] += packet_size

        protocol = "OUTROS"
        destination_port = None

        # ---------------------------------------------
        # TCP
        # ---------------------------------------------

        if TCP in packet:

            protocol = "TCP"

            destination_port = int(packet[TCP].dport)

            flow = (
                source_ip,
                destination_ip,
                "TCP",
                int(packet[TCP].sport),
                destination_port,
            )

        # ---------------------------------------------
        # UDP
        # ---------------------------------------------

        elif UDP in packet:

            protocol = "UDP"

            destination_port = int(packet[UDP].dport)

            flow = (
                source_ip,
                destination_ip,
                "UDP",
                int(packet[UDP].sport),
                destination_port,
            )

        # ---------------------------------------------
        # ICMP
        # ---------------------------------------------

        elif ICMP in packet:

            protocol = "ICMP"

            flow = (
                source_ip,
                destination_ip,
                "ICMP",
                None,
                None,
            )

        else:

            flow = (
                source_ip,
                destination_ip,
                protocol,
                None,
                None,
            )

        transport_protocols[protocol] += 1
        stats["protocols"][protocol] += 1

        # ---------------------------------------------
        # PORTAS DE DESTINO
        # ---------------------------------------------

        if destination_port is not None:

            destination_ports[destination_port] += 1

            stats["destination_ports"][destination_port] += 1

        # ---------------------------------------------
        # FLUXOS DISTINTOS
        # ---------------------------------------------

        stats["flows"].add(flow)

    # =================================================
    # 5. CONSOLIDACAO POR DISPOSITIVO
    # =================================================

    devices = []

    for ip, stats in device_stats.items():

        flows = stats["flows"]

        devices.append({
            "ip": ip,

            "packet_count": stats["packet_count"],

            "bytes_transferred": stats["bytes_transferred"],

            # Quantidade de fluxos distintos observados.
            "connection_count": len(flows),

            "distinct_destination_ports": len(
                stats["destination_ports"]
            ),

            "destination_ports": [
                {
                    "port": port,
                    "packets": count,
                }
                for port, count in
                stats["destination_ports"].most_common()
            ],

            "protocols": dict(stats["protocols"]),
        })

    devices.sort(
        key=lambda item: item["packet_count"],
        reverse=True,
    )

    # =================================================
    # 6. RESULTADO DA ANALISE
    # =================================================

    return {
        "total_packets": len(packets),

        "total_bytes": total_bytes,

        "network_protocols": dict(network_protocols),

        "transport_protocols": dict(transport_protocols),

        # Compatibilidade com o frontend antigo.
        "protocols": {
            **dict(network_protocols),
            **dict(transport_protocols),
        },

        "top_sources": [
            {
                "ip": ip,
                "packets": count,
            }
            for ip, count in source_ips.most_common(10)
        ],

        "top_destinations": [
            {
                "ip": ip,
                "packets": count,
            }
            for ip, count in destination_ips.most_common(10)
        ],

        "top_ports": [
            {
                "port": port,
                "packets": count,
            }
            for port, count in destination_ports.most_common(10)
        ],

        # NOVO: estatisticas individuais por IP.
        "device_stats": devices,
    }
