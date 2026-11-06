
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# =====================================================
# 1. DEFINIÇÃO DAS VARIÁVEIS FUZZY
# =====================================================

# Entradas normalizadas de 0 a 100.

packets = ctrl.Antecedent(
    np.arange(0, 101, 1),
    "packets"
)

ports = ctrl.Antecedent(
    np.arange(0, 101, 1),
    "ports"
)

traffic = ctrl.Antecedent(
    np.arange(0, 101, 1),
    "traffic"
)

# Saída: índice de risco de 0 a 100.

risk = ctrl.Consequent(
    np.arange(0, 101, 1),
    "risk"
)


# =====================================================
# 2. FUNÇÕES DE PERTINÊNCIA
# =====================================================

# Frequência de pacotes
packets["low"] = fuzz.trimf(
    packets.universe,
    [0, 0, 40]
)

packets["medium"] = fuzz.trimf(
    packets.universe,
    [20, 50, 80]
)

packets["high"] = fuzz.trimf(
    packets.universe,
    [60, 100, 100]
)


# Quantidade de portas suspeitas
ports["few"] = fuzz.trimf(
    ports.universe,
    [0, 0, 40]
)

ports["medium"] = fuzz.trimf(
    ports.universe,
    [20, 50, 80]
)

ports["many"] = fuzz.trimf(
    ports.universe,
    [60, 100, 100]
)


# Volume de tráfego anormal
traffic["normal"] = fuzz.trimf(
    traffic.universe,
    [0, 0, 40]
)

traffic["suspicious"] = fuzz.trimf(
    traffic.universe,
    [20, 50, 80]
)

traffic["abnormal"] = fuzz.trimf(
    traffic.universe,
    [60, 100, 100]
)


# =====================================================
# 3. CLASSIFICAÇÃO FUZZY DO RISCO
# =====================================================

risk["low"] = fuzz.trimf(
    risk.universe,
    [0, 0, 35]
)

risk["medium"] = fuzz.trimf(
    risk.universe,
    [20, 50, 80]
)

risk["high"] = fuzz.trimf(
    risk.universe,
    [65, 100, 100]
)


# =====================================================
# 4. BASE DE REGRAS FUZZY
# =====================================================

rules = [

    # Combinação de indicadores elevados
    ctrl.Rule(
        packets["high"] & ports["many"],
        risk["high"]
    ),

    ctrl.Rule(
        packets["high"] & traffic["abnormal"],
        risk["high"]
    ),

    ctrl.Rule(
        ports["many"] & traffic["abnormal"],
        risk["high"]
    ),

    # Indicadores intermediários
    ctrl.Rule(
        packets["medium"] | ports["medium"],
        risk["medium"]
    ),

    ctrl.Rule(
        traffic["suspicious"],
        risk["medium"]
    ),

    # Condições normais
    ctrl.Rule(
        packets["low"] &
        ports["few"] &
        traffic["normal"],
        risk["low"]
    ),

    # Tráfego suspeito mesmo com poucos pacotes e portas
    ctrl.Rule(
        packets["low"] &
        ports["few"] &
        traffic["suspicious"],
        risk["medium"]
    ),

    # Indicadores individualmente elevados
    ctrl.Rule(
        packets["high"],
        risk["high"]
    ),

    ctrl.Rule(
        ports["many"],
        risk["high"]
    ),

    ctrl.Rule(
        traffic["abnormal"],
        risk["high"]
    ),
]


# =====================================================
# 5. CONSTRUÇÃO DO SISTEMA DE INFERÊNCIA
# =====================================================

system = ctrl.ControlSystem(rules)


# =====================================================
# 6. VALIDAÇÃO DAS ENTRADAS
# =====================================================

def validate_score(value: float, field_name: str) -> float:
    """
    Valida e normaliza um indicador entre 0 e 100.
    """

    try:
        value = float(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} deve ser um valor numérico."
        ) from error

    if not np.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(
            f"{field_name} deve estar entre 0 e 100."
        )

    return value


# =====================================================
# 7. CÁLCULO DO ÍNDICE DE RISCO
# =====================================================

def calculate_risk(
    packet_score: float,
    port_score: float,
    traffic_score: float
) -> float:
    """
    Calcula o índice de risco utilizando inferência Fuzzy.

    Entradas:
        packet_score: frequência de pacotes (0-100).
        port_score: indicador de portas suspeitas (0-100).
        traffic_score: indicador de tráfego anormal (0-100).

    Retorno:
        Índice de risco entre 0 e 100.
    """

    packet_score = validate_score(
        packet_score,
        "packet_score"
    )

    port_score = validate_score(
        port_score,
        "port_score"
    )

    traffic_score = validate_score(
        traffic_score,
        "traffic_score"
    )

    simulation = ctrl.ControlSystemSimulation(system)

    simulation.input["packets"] = packet_score
    simulation.input["ports"] = port_score
    simulation.input["traffic"] = traffic_score

    try:
        simulation.compute()

        score = float(simulation.output["risk"])

    except Exception as error:
        raise RuntimeError(
            "Não foi possível executar a inferência Fuzzy."
        ) from error

    return round(score, 2)


# =====================================================
# 8. CLASSIFICAÇÃO FINAL DO RISCO
# =====================================================

def classify_risk(score: float) -> str:
    """
    Classifica o índice de risco.

    0 a 39.99  -> baixo
    40 a 69.99 -> moderado
    70 a 100   -> critico
    """

    score = validate_score(score, "score")

    if score >= 70:
        return "critico"

    if score >= 40:
        return "moderado"

    return "baixo"


# =====================================================
# 9. RESULTADO COMPLETO PARA A APLICAÇÃO
# =====================================================

def analyze_risk(
    packet_score: float,
    port_score: float,
    traffic_score: float
) -> dict:
    """
    Retorna o resultado completo para integração
    com dispositivos, eventos e alertas.
    """

    score = calculate_risk(
        packet_score=packet_score,
        port_score=port_score,
        traffic_score=traffic_score
    )

    classification = classify_risk(score)

    return {
        "risk_score": score,
        "classification": classification,
        "indicators": {
            "packets": packet_score,
            "ports": port_score,
            "traffic": traffic_score
        }
    }
