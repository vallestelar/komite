from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tortoise.transactions import in_transaction

from app.dbs.postgres.context import DbContext


async def _count(conn, table: str, condominium_id: str) -> int:
    rows = await conn.execute_query_dict(
        f"SELECT COUNT(*)::int AS count FROM {table} WHERE condominium_id=$1",
        [condominium_id],
    )
    return rows[0]["count"]


async def move_units_and_contacts(source_id: str, dest_id: str, updated_by: str) -> None:
    db = DbContext()
    await db.init()
    try:
        async with in_transaction("default") as conn:
            source_units = await _count(conn, "units", source_id)
            source_contacts = await _count(conn, "unit_contacts", source_id)
            dest_units = await _count(conn, "units", dest_id)
            dest_contacts = await _count(conn, "unit_contacts", dest_id)

            print(
                "before "
                f"source_units={source_units} source_contacts={source_contacts} "
                f"dest_units={dest_units} dest_contacts={dest_contacts}"
            )

            if dest_units or dest_contacts:
                raise RuntimeError("Destination condominium already has units or contacts.")
            if not source_units and not source_contacts:
                raise RuntimeError("Source condominium has no units or contacts to move.")

            await conn.execute_query(
                """
                UPDATE unit_contacts
                   SET condominium_id=$1, updated_at=NOW(), updated_by=$3
                 WHERE condominium_id=$2
                """,
                [dest_id, source_id, updated_by],
            )
            await conn.execute_query(
                """
                UPDATE units
                   SET condominium_id=$1, updated_at=NOW(), updated_by=$3
                 WHERE condominium_id=$2
                """,
                [dest_id, source_id, updated_by],
            )

            source_units_after = await _count(conn, "units", source_id)
            source_contacts_after = await _count(conn, "unit_contacts", source_id)
            dest_units_after = await _count(conn, "units", dest_id)
            dest_contacts_after = await _count(conn, "unit_contacts", dest_id)

            print(
                "after "
                f"source_units={source_units_after} source_contacts={source_contacts_after} "
                f"dest_units={dest_units_after} dest_contacts={dest_contacts_after}"
            )
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Move units and unit contacts between condominiums.")
    parser.add_argument("--source", required=True, help="Source condominium UUID")
    parser.add_argument("--dest", required=True, help="Destination condominium UUID")
    parser.add_argument("--updated-by", default="maintenance_move_condominium_data")
    args = parser.parse_args()

    asyncio.run(move_units_and_contacts(args.source, args.dest, args.updated_by))


if __name__ == "__main__":
    main()
