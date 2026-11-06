
import ipaddress
import logging
import time

from scapy.all import ARP, Ether, srp, conf


logger = logging.getLogger("sentinelhome.discovery")


# =====================================================
# CONFIGURACOES
# =====================================================

DEFAULT_TIMEOUT = 2
MAX_TIMEOUT = 10
MIN_TIMEOUT = 1
MAX_HOSTS = 1024


# =====================================================
# VALIDACAO DA REDE
# =====================================================

def validate_network(network: str):
    """
    Valida a faixa IPv4 informada.

    A descoberta deve ser executada somente em redes
    que o operador possui autorizacao para monitorar.
    """

    try:
        parsed_network = ipaddress.ip_network(
            network,
            strict=False,
        )

    except ValueError as error:
        raise ValueError(
            "Informe uma rede IPv4 valida. "
            "Exemplo: 192.168.0.0/24"
        ) from error

    if parsed_network.version != 4:
        raise ValueError(
            "A descoberta ARP suporta somente redes IPv4."
        )

    if parsed_network.num_addresses > MAX_HOSTS:
        raise ValueError(
            f"A faixa excede o limite de {MAX_HOSTS} enderecos."
        )

    if parsed_network.is_multicast or parsed_network.is_unspecified:
        raise ValueError(
            "A faixa informada nao e adequada para descoberta ARP."
        )

    return parsed_network


# =====================================================
# DESCOBERTA DE DISPOSITIVOS
# =====================================================

def discover_devices(
    network: str,
    timeout: int = DEFAULT_TIMEOUT,
    interface: str = None,
):
    """
    Descobre dispositivos ativos em uma rede IPv4
    utilizando requisicoes ARP.

    Exemplo:
        discover_devices("192.168.0.0/24")

    Retorna:
        - Faixa de rede consultada
        - Total de dispositivos encontrados
        - Lista de IPs e MACs identificados
        - Tempo de execucao

    Observacao:
        A funcao nao cadastra automaticamente os
        dispositivos no banco de dados.
    """

    parsed_network = validate_network(network)

    if not isinstance(timeout, (int, float)) or not (
        MIN_TIMEOUT <= timeout <= MAX_TIMEOUT
    ):
        raise ValueError(
            f"O timeout deve estar entre "
            f"{MIN_TIMEOUT} e {MAX_TIMEOUT} segundos."
        )

    hosts = list(parsed_network.hosts())

    if not hosts:
        raise ValueError(
            "A faixa informada nao possui enderecos para consultar."
        )

    logger.info(
        "Iniciando descoberta ARP na rede %s",
        parsed_network,
    )

    started_at = time.perf_counter()

    # Uma requisicao ARP para toda a faixa.
    arp_request = ARP(
        pdst=str(parsed_network)
    )

    ethernet_frame = Ether(
        dst="ff:ff:ff:ff:ff:ff"
    )

    packet = ethernet_frame / arp_request

    try:
        answered, unanswered = srp(
            packet,
            timeout=float(timeout),
            iface=interface,
            verbose=False,
            retry=1,
        )

    except PermissionError as error:
        logger.exception(
            "Permissao insuficiente para executar descoberta ARP."
        )

        raise RuntimeError(
            "Permissao insuficiente. Execute o backend "
            "com privilegios adequados e verifique o Npcap."
        ) from error

    except Exception as error:
        logger.exception(
            "Falha durante a descoberta da rede %s",
            parsed_network,
        )

        raise RuntimeError(
            "Nao foi possivel realizar a descoberta ARP. "
            "Verifique a interface de rede e o Npcap."
        ) from error

    discovered = []
    processed_ips = set()

    for sent, received in answered:

        ip_address = received.psrc
        mac_address = received.hwsrc.lower()

        if ip_address in processed_ips:
            continue

        processed_ips.add(ip_address)

        discovered.append({
            "ip_address": ip_address,
            "mac_address": mac_address,
            "status": "online",
            "discovery_method": "ARP",
        })

    discovered.sort(
        key=lambda device: ipaddress.ip_address(
            device["ip_address"]
        )
    )

    elapsed = round(
        time.perf_counter() - started_at,
        3,
    )

    logger.info(
        "Descoberta concluida: %s dispositivos encontrados em %.3f segundos.",
        len(discovered),
        elapsed,
    )

    return {
        "network": str(parsed_network),
        "total_hosts": len(hosts),
        "total_found": len(discovered),
        "total_unanswered": len(unanswered),
        "scan_duration_seconds": elapsed,
        "devices": discovered,
    }
