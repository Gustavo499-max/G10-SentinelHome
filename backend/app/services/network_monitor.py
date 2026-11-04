
from collections import Counter
from pathlib import Path

from scapy.all import IP, IPv6, TCP, UDP, rdpcap


def analyze_pcap(file_path: str):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("Arquivo de captura nao encontrado.")

    if path.suffix.lower() not in {".pcap", ".pcapng"}:
        raise ValueError("Formato permitido: PCAP ou PCAPNG.")

    packets = rdpcap(str(path))

    source_ips = Counter()
    destination_ips = Counter()
    destination_ports = Counter()
    protocols = Counter()

    for packet in packets:
        if IP in packet:
            source_ips[packet[IP].src] += 1
            destination_ips[packet[IP].dst] += 1
            protocols["IPv4"] += 1

        elif IPv6 in packet:
            source_ips[packet[IPv6].src] += 1
            destination_ips[packet[IPv6].dst] += 1
            protocols["IPv6"] += 1

        if TCP in packet:
            protocols["TCP"] += 1
            destination_ports[int(packet[TCP].dport)] += 1

        elif UDP in packet:
            protocols["UDP"] += 1
            destination_ports[int(packet[UDP].dport)] += 1

        else:
            protocols["OUTROS"] += 1

    return {
        "total_packets": len(packets),
        "protocols": dict(protocols),
        "top_sources": [
            {"ip": ip, "packets": count}
            for ip, count in source_ips.most_common(10)
        ],
        "top_destinations": [
            {"ip": ip, "packets": count}
            for ip, count in destination_ips.most_common(10)
        ],
        "top_ports": [
            {"port": port, "packets": count}
            for port, count in destination_ports.most_common(10)
        ]
    }
