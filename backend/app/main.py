
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
import logging
import os

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.routes import devices, alerts, analytics

from app.services.fuzzy_engine import (
    calculate_risk,
    classify_risk,
)

from app.services.network_monitor import analyze_pcap
from app.services.network_discovery import discover_devices

from app.services.risk_analyzer import (
    analyze_capture_for_devices,
)


# =====================================================
# 1. CONFIGURACOES GERAIS
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("sentinelhome")

MAX_UPLOAD_SIZE = 20 * 1024 * 1024

ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
]


# =====================================================
# 2. CICLO DE VIDA DA APLICACAO
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Iniciando G10 SentinelHome...")

    try:
        Base.metadata.create_all(bind=engine)

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Banco de dados inicializado com sucesso.")

        yield

    except Exception:
        logger.exception("Erro durante a execucao da aplicacao.")
        raise

    finally:
        engine.dispose()
        logger.info("G10 SentinelHome encerrado.")


# =====================================================
# 3. INSTANCIA FASTAPI
# =====================================================

app = FastAPI(
    title="G10 SentinelHome API",
    description=(
        "Plataforma inteligente para monitoramento, "
        "analise e seguranca de redes domesticas."
    ),
    version="1.5.0",
    lifespan=lifespan,
)


# =====================================================
# 4. CONFIGURACAO CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# 5. REGISTRO DAS ROTAS
# =====================================================

app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(analytics.router)


# =====================================================
# 6. ROTA PRINCIPAL
# =====================================================

@app.get("/")
def home():

    return {
        "project": "G10 SentinelHome",
        "status": "online",
        "version": "1.5.0",
        "description": "Intelligent Network Monitoring Platform",
        "modules": [
            "device_management",
            "security_alerts",
            "risk_analysis",
            "fuzzy_inference",
            "pcap_analysis",
            "device_risk_analysis",
            "network_topology",
            "geographic_threat_intelligence",
        ],
        "documentation": "/docs",
    }


# =====================================================
# 7. VERIFICACAO DE SAUDE
# =====================================================

@app.get("/api/health")
def health():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": "G10 SentinelHome",
            "api": "connected",
            "database": "connected",
        }

    except Exception as error:

        logger.exception(
            "Falha na verificacao de saude da aplicacao."
        )

        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
            },
        ) from error


# =====================================================
# 8. MOTOR DE INTELIGENCIA COMPUTACIONAL FUZZY
# =====================================================

@app.get("/api/risk")
def risk(
    packets: float = 30,
    ports: float = 20,
    traffic: float = 25,
):

    try:
        score = calculate_risk(
            packets,
            ports,
            traffic,
        )

        level = classify_risk(score)

        return {
            "risk_score": score,
            "risk_level": level,
            "inputs": {
                "packets": packets,
                "ports": ports,
                "traffic": traffic,
            },
        }

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:

        logger.exception("Falha no calculo Fuzzy.")

        raise HTTPException(
            status_code=500,
            detail="Falha ao calcular o risco Fuzzy.",
        ) from error


# =====================================================
# 9. ANALISE GERAL DE CAPTURAS PCAP / PCAPNG
# =====================================================

@app.post("/api/network/analyze")
async def upload_capture(
    file: UploadFile = File(...),
):

    filename = Path(file.filename or "capture").name
    extension = Path(filename).suffix.lower()

    if extension not in {".pcap", ".pcapng"}:

        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo PCAP ou PCAPNG.",
        )

    temporary_path = None

    try:
        content = await file.read(MAX_UPLOAD_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="O arquivo esta vazio.",
            )

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Limite maximo de arquivo: 20 MB.",
            )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary:

            temporary.write(content)
            temporary_path = temporary.name

        logger.info(
            "Iniciando analise geral da captura: %s",
            filename,
        )

        result = analyze_pcap(temporary_path)

        return {
            "status": "success",
            "filename": filename,
            "analysis": result,
        }

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        logger.exception(
            "Erro durante a analise da captura."
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Nao foi possivel analisar a captura. "
                "Verifique o arquivo enviado."
            ),
        ) from error

    finally:
        await file.close()

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


# =====================================================
# 10. ANALISE FUZZY VINCULADA AOS DISPOSITIVOS
# =====================================================

@app.post("/api/network/analyze-devices")
async def upload_capture_for_devices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    filename = Path(file.filename or "capture").name
    extension = Path(filename).suffix.lower()

    if extension not in {".pcap", ".pcapng"}:

        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo PCAP ou PCAPNG.",
        )

    temporary_path = None

    try:

        # ---------------------------------------------
        # VALIDACAO DO ARQUIVO
        # ---------------------------------------------

        content = await file.read(MAX_UPLOAD_SIZE + 1)

        if not content:

            raise HTTPException(
                status_code=400,
                detail="O arquivo esta vazio.",
            )

        if len(content) > MAX_UPLOAD_SIZE:

            raise HTTPException(
                status_code=413,
                detail="Limite maximo de arquivo: 20 MB.",
            )

        # ---------------------------------------------
        # ARQUIVO TEMPORARIO
        # ---------------------------------------------

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary:

            temporary.write(content)
            temporary_path = temporary.name

        logger.info(
            "Iniciando analise Fuzzy por dispositivo: %s",
            filename,
        )

        # ---------------------------------------------
        # ANALISE INTEGRADA
        # ---------------------------------------------

        result = analyze_capture_for_devices(
            db=db,
            file_path=temporary_path,
        )

        logger.info(
            "Analise Fuzzy concluida. Dispositivos: %s",
            result["devices_analyzed"],
        )

        return {
            "status": "success",
            "filename": filename,
            "analysis": result,
        }

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        logger.exception(
            "Erro durante a analise Fuzzy por dispositivo."
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Nao foi possivel processar a captura "
                "e atualizar os dispositivos."
            ),
        ) from error

    finally:

        await file.close()

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


# =====================================================
# 11. DESCOBERTA DE DISPOSITIVOS NA REDE LOCAL
# =====================================================

@app.post("/api/network/discover")
def discover_network(
    network: str,
    timeout: int = 2,
    interface: str = None,
):
    """
    Executa descoberta ARP na rede local autorizada.

    Exemplo:
        POST /api/network/discover?network=192.168.0.0/24
    """

    try:
        result = discover_devices(
            network=network,
            timeout=timeout,
            interface=interface,
        )

        logger.info(
            "Descoberta concluida: %s dispositivos encontrados.",
            result["total_found"],
        )

        return {
            "status": "success",
            "message": "Descoberta de rede concluida.",
            "discovery": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        logger.exception(
            "Falha na descoberta da rede."
        )

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:

        logger.exception(
            "Erro inesperado na descoberta de dispositivos."
        )

        raise HTTPException(
            status_code=500,
            detail="Erro interno durante a descoberta da rede.",
        ) from error
