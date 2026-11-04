
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

from app.database import Base, engine
from app import models
from app.routes import devices, alerts, analytics
from app.services.fuzzy_engine import calculate_risk, classify_risk
from app.services.network_monitor import analyze_pcap

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="G10 SentinelHome API",
    description="Monitoramento inteligente de redes domesticas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(analytics.router)


@app.get("/")
def home():
    return {
        "project": "G10 SentinelHome",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/api/risk")
def risk(
    packets: float = 30,
    ports: float = 20,
    traffic: float = 25
):
    values = [packets, ports, traffic]

    if any(not 0 <= value <= 100 for value in values):
        raise HTTPException(
            422,
            "Todos os valores devem estar entre 0 e 100."
        )

    try:
        score = calculate_risk(packets, ports, traffic)
    except (ValueError, Exception) as error:
        raise HTTPException(422, f"Falha no calculo Fuzzy: {error}")

    return {
        "risk_score": score,
        "risk_level": classify_risk(score)
    }


@app.post("/api/network/analyze")
async def upload_capture(file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in {".pcap", ".pcapng"}:
        raise HTTPException(400, "Envie um arquivo PCAP ou PCAPNG.")

    content = await file.read()

    if not content:
        raise HTTPException(400, "O arquivo esta vazio.")

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "Limite de arquivo: 20 MB.")

    temporary_path = None

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False
        ) as temporary:
            temporary.write(content)
            temporary_path = temporary.name

        return analyze_pcap(temporary_path)

    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(400, str(error))

    except Exception:
        raise HTTPException(
            422,
            "Nao foi possivel analisar a captura. Verifique o arquivo."
        )

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
