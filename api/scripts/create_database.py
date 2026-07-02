import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg2
from psycopg2 import sql

from app.core.settings import settings


def main() -> int:
    print(
        "Creando/verificando base:",
        f"{settings.postgres_db} en {settings.postgres_host}:{settings.postgres_port}",
    )
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            dbname="postgres",
            connect_timeout=5,
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.postgres_db,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"OK: la base '{settings.postgres_db}' ya existe.")
                return 0

            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.postgres_db)))
            print(f"OK: base '{settings.postgres_db}' creada.")
            return 0
    except Exception as exc:
        detail = str(exc).strip() or repr(exc)
        print(f"ERROR: {type(exc).__name__}: {detail}")
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

