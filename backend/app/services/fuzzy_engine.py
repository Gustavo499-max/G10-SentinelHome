
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

packets = ctrl.Antecedent(
    np.arange(0, 101, 1), "packets"
)

ports = ctrl.Antecedent(
    np.arange(0, 101, 1), "ports"
)

traffic = ctrl.Antecedent(
    np.arange(0, 101, 1), "traffic"
)

risk = ctrl.Consequent(
    np.arange(0, 101, 1), "risk"
)

packets["low"] = fuzz.trimf(
    packets.universe, [0, 0, 40]
)
packets["medium"] = fuzz.trimf(
    packets.universe, [20, 50, 80]
)
packets["high"] = fuzz.trimf(
    packets.universe, [60, 100, 100]
)

ports["few"] = fuzz.trimf(
    ports.universe, [0, 0, 40]
)
ports["moderate"] = fuzz.trimf(
    ports.universe, [20, 50, 80]
)
ports["many"] = fuzz.trimf(
    ports.universe, [60, 100, 100]
)

traffic["normal"] = fuzz.trimf(
    traffic.universe, [0, 0, 40]
)
traffic["suspicious"] = fuzz.trimf(
    traffic.universe, [20, 50, 80]
)
traffic["abnormal"] = fuzz.trimf(
    traffic.universe, [60, 100, 100]
)

risk["low"] = fuzz.trimf(
    risk.universe, [0, 0, 35]
)
risk["medium"] = fuzz.trimf(
    risk.universe, [20, 50, 80]
)
risk["high"] = fuzz.trimf(
    risk.universe, [65, 100, 100]
)

rules = [
    ctrl.Rule(
        packets["high"] & ports["many"],
        risk["high"]
    ),
    ctrl.Rule(
        traffic["abnormal"],
        risk["high"]
    ),
    ctrl.Rule(
        packets["medium"] | ports["moderate"],
        risk["medium"]
    ),
    ctrl.Rule(
        packets["low"] & ports["few"] & traffic["normal"],
        risk["low"]
    )
]

system = ctrl.ControlSystem(rules)


def calculate_risk(packet_score, port_score, traffic_score):
    simulation = ctrl.ControlSystemSimulation(system)

    simulation.input["packets"] = packet_score
    simulation.input["ports"] = port_score
    simulation.input["traffic"] = traffic_score

    simulation.compute()

    return round(float(simulation.output["risk"]), 2)
