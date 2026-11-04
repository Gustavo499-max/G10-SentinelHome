
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.fuzzy_engine import calculate_risk

app = FastAPI(
    title="G10 SentinelHome API",
    description="Sistema inteligente de monitoramento de redes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():
    return {
        "project": "G10 SentinelHome",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/risk")
def risk(
    packets: float = 30,
    ports: float = 20,
    traffic: float = 25
):
    values = [packets, ports, traffic]

    if any(value < 0 or value > 100 for value in values):
        return {"error": "Valores devem estar entre 0 e 100"}

    score = calculate_risk(packets, ports, traffic)

    if score >= 70:
        level = "CRITICO"
    elif score >= 40:
        level = "MODERADO"
    else:
        level = "BAIXO"

    return {
        "risk_score": score,
        "risk_level": level
    }
