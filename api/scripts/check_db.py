import asyncio
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncpg
import psycopg2
from psycopg2 import OperationalError

from app.core.settings import settings
from app.dbs.postgres.context import DbContext


def check_tcp_port() -> bool:
    try:
        with socket.create_connection(
            (settings.postgres_host, settings.postgres_port),
            timeout=5,
        ):
            print("TCP: OK, el puerto PostgreSQL responde.")
            return True
    except Exception as exc:
        print(f"TCP: ERROR: {type(exc).__name__}: {exc}")
        return False


def _format_exception(exc: Exception) -> str:
    detail = str(exc).strip()
    if detail:
        return detail
    return repr(exc)


def check_psycopg2(database: str | None = None) -> bool:
    dbname = database or settings.postgres_db
    try:
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            dbname=dbname,
            connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
        conn.close()
        print(f"psycopg2 ({dbname}): OK: {version}")
        return True
    except OperationalError as exc:
        print(f"psycopg2 ({dbname}): ERROR: {type(exc).__name__}: {_format_exception(exc)}")
        if getattr(exc, "pgcode", None):
            print(f"psycopg2 ({dbname}): pgcode={exc.pgcode}")
        if getattr(exc, "diag", None) and getattr(exc.diag, "message_primary", None):
            print(f"psycopg2 ({dbname}): detail={exc.diag.message_primary}")
        return False
    except Exception as exc:
        print(f"psycopg2 ({dbname}): ERROR: {type(exc).__name__}: {_format_exception(exc)}")
        return False


async def check_asyncpg(database: str | None = None) -> bool:
    dbname = database or settings.postgres_db
    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=dbname,
            timeout=5,
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        print(f"asyncpg ({dbname}): OK: {version}")
        return True
    except Exception as exc:
        print(f"asyncpg ({dbname}): ERROR: {type(exc).__name__}: {_format_exception(exc)}")
        return False


async def check_tortoise() -> bool:
    db = DbContext()
    try:
        await db.init(generate_schemas=False)
        result = await db.check_connection()
        print(f"Tortoise: {result}")
        return bool(result.get("success"))
    except Exception as exc:
        print(f"Tortoise: ERROR: {type(exc).__name__}: {exc}")
        return False
    finally:
        await db.close()


async def main() -> int:
    print(
        "Probando PostgreSQL:",
        f"{settings.postgres_user}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}",
    )
    print("-" * 72)

    tcp_ok = check_tcp_port()
    psycopg2_ok = check_psycopg2() if tcp_ok else False
    asyncpg_ok = await check_asyncpg() if tcp_ok else False

    if tcp_ok and not psycopg2_ok and settings.postgres_db != "postgres":
        print("-" * 72)
        print("Probando conexion contra la base administrativa 'postgres'...")
        check_psycopg2("postgres")
        await check_asyncpg("postgres")

    tortoise_ok = await check_tortoise() if asyncpg_ok else False

    print("-" * 72)
    if tcp_ok and psycopg2_ok and asyncpg_ok and tortoise_ok:
        print("Resultado: OK, la API deberia poder conectar.")
        return 0

    print("Resultado: ERROR, revisa la primera capa que falle arriba.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
