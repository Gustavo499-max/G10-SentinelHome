
from sqlalchemy import inspect, text

from app.database import engine


def migrate_database():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ["devices", "alerts", "network_events"]

    for table in required_tables:
        if table not in tables:
            print(f"Tabela {table} não encontrada.")
            print("Verifique a inicialização do banco de dados.")
            return

    # ==========================================
    # 1. MIGRAÇÃO DA TABELA DEVICES
    # ==========================================

    device_columns = {
        column["name"]
        for column in inspector.get_columns("devices")
    }

    device_migrations = {
        "risk_updated_at": "DATETIME",
        "risk_source": "VARCHAR(20)",
    }

    with engine.begin() as connection:
        for column_name, column_type in device_migrations.items():

            if column_name not in device_columns:
                print(f"Adicionando devices.{column_name}...")

                connection.execute(
                    text(
                        f"""
                        ALTER TABLE devices
                        ADD COLUMN {column_name} {column_type}
                        """
                    )
                )

                print(f"Coluna {column_name} adicionada!")

            else:
                print(f"Coluna {column_name} já existe.")

    # ==========================================
    # 2. MIGRAÇÃO DA TABELA ALERTS
    # ==========================================

    inspector = inspect(engine)

    alert_columns = {
        column["name"]
        for column in inspector.get_columns("alerts")
    }

    if "device_id" not in alert_columns:
        print("Adicionando alerts.device_id...")

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE alerts
                    ADD COLUMN device_id INTEGER
                    REFERENCES devices(id) ON DELETE SET NULL
                    """
                )
            )

        print("Coluna alerts.device_id adicionada!")

    else:
        print("Coluna alerts.device_id já existe.")

    # ==========================================
    # 3. VERIFICAR ÍNDICE
    # ==========================================

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_alerts_device_id
                ON alerts (device_id)
                """
            )
        )

    print("\nMigração concluída com sucesso!")
    print("Banco de dados preservado.")


if __name__ == "__main__":
    migrate_database()
