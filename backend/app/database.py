
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


# =====================================================
# CONFIGURAÇÃO DE DIRETÓRIOS
# =====================================================

# Caminho principal do projeto
BASE_DIR = Path(__file__).resolve().parents[2]

# Diretório de armazenamento do banco
DATABASE_DIR = BASE_DIR / "data"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# Banco de dados SQLite
DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'sentinelhome.db'}"


# =====================================================
# CONFIGURAÇÃO DO ENGINE
# =====================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    pool_pre_ping=True,
)


# =====================================================
# CHAVES ESTRANGEIRAS DO SQLITE
# =====================================================

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    """
    Habilita a integridade referencial do SQLite
    em cada nova conexão.
    """

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


# =====================================================
# GERENCIAMENTO DE SESSÕES
# =====================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# =====================================================
# BASE DOS MODELOS SQLALCHEMY
# =====================================================

Base = declarative_base()


# =====================================================
# DEPENDÊNCIA PARA FASTAPI
# =====================================================

def get_db():
    """
    Cria uma sessão para cada requisição
    e garante seu fechamento ao finalizar.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
