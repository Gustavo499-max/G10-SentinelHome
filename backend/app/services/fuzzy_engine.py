
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


packets = ctrl.Antecedent(np.arange(0, 101, 1), "packets")
ports = ctrl.Antecedent(np.arange(0, 101, 1), "ports")
traffic = ctrl.Antecedent(np.arange(0, 101, 1), "traffic")

risk = ctrl.Consequent(np.arange(0, 101, 1), "risk")

# Frequencia de pacotes
packets["low"] = fuzz.trimf(packets.universe, [0, 0, 40])
packets["medium"] = fuzz.trimf(packets.universe, [20, 50, 80])
packets["high"] = fuzz.trimf(packets.universe, [60, 100, 100])

# Quantidade de portas suspeitas
ports["few"] = fuzz.trimf(ports.universe, [0, 0, 40])
ports["medium"] = fuzz.trimf(ports.universe, [20, 50, 80])
ports["many"] = fuzz.trimf(ports.universe, [60, 100, 100])

# Volume de trafego anormal
traffic["normal"] = fuzz.trimf(traffic.universe, [0, 0, 40])
traffic["suspicious"] = fuzz.trimf(traffic.universe, [20, 50, 80])
traffic["abnormal"] = fuzz.trimf(traffic.universe, [60, 100, 100])

# Classificacao do risco
risk["low"] = fuzz.trimf(risk.universe, [0, 0, 35])
risk["medium"] = fuzz.trimf(risk.universe, [20, 50, 80])
risk["high"] = fuzz.trimf(risk.universe, [65, 100, 100])

rules = [
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
    ctrl.Rule(
        packets["medium"] | ports["medium"] | traffic["suspicious"],
        risk["medium"]
    ),
    ctrl.Rule(
        packets["low"] & ports["few"] & traffic["normal"],
        risk["low"]
    ),
    ctrl.Rule(
        packets["low"] & ports["few"] & traffic["suspicious"],
        risk["medium"]
    ),
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
    )
]

system = ctrl.ControlSystem(rules)


def calculate_risk(packet_score, port_score, traffic_score):
    values = [packet_score, port_score, traffic_score]

    if any(not np.isfinite(v) or v < 0 or v > 100 for v in values):
        raise ValueError("As entradas devem estar entre 0 e 100.")

    simulation = ctrl.ControlSystemSimulation(system)

    simulation.input["packets"] = packet_score
    simulation.input["ports"] = port_score
    simulation.input["traffic"] = traffic_score

    simulation.compute()

    return round(float(simulation.output["risk"]), 2)


def classify_risk(score):
    if score >= 70:
        return "critico"
    if score >= 40:
        return "moderado"
    return "baixo"
