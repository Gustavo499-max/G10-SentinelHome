
from sqlalchemy import inspect, text

from app.database import engine


def migrate_database():
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if "alerts" not in tables:
        print("Tabela alerts não encontrada.")
        return

    if "devices" not in tables:
        print("Tabela devices não encontrada.")
        return

    columns = [
        column["name"]
        for column in inspector.get_columns("alerts")
    ]

    if "device_id" not in columns:

        print("Adicionando coluna device_id...")

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

        print("Coluna device_id adicionada!")

    else:
        print("Coluna device_id já existe.")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_alerts_device_id
                ON alerts (device_id)
                """
            )
        )

    print("Índice verificado!")
    print("Migração concluída com sucesso!")


if __name__ == "__main__":
    migrate_database()
