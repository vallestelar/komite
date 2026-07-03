from tortoise import BaseDBAsyncClient


TENANT_TABLES = {
    "buildings": "CASCADE",
    "units": "CASCADE",
    "incidents": "CASCADE",
    "incident_events": "CASCADE",
    "tasks": "CASCADE",
    "task_checklists": "CASCADE",
    "inspections": "CASCADE",
    "inspection_answers": "CASCADE",
    "reports": "CASCADE",
    "report_versions": "CASCADE",
    "communications": "CASCADE",
    "communication_recipients": "CASCADE",
    "attachments": "CASCADE",
    "user_condominiums": "CASCADE",
    "audit_logs": "SET NULL",
    "ai_requests": "SET NULL",
    "notification_logs": "SET NULL",
}


def _add_company_columns_sql() -> str:
    statements: list[str] = []
    for table, on_delete in TENANT_TABLES.items():
        constraint = f"{table}_company_id_fkey"
        index = f"idx_{table}_company_id"
        statements.append(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "company_id" UUID;')
        statements.append(
            f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = '{constraint}'
    ) THEN
        ALTER TABLE "{table}"
            ADD CONSTRAINT "{constraint}"
            FOREIGN KEY ("company_id") REFERENCES "companies" ("id")
            ON DELETE {on_delete};
    END IF;
END $$;
"""
        )
        statements.append(f'CREATE INDEX IF NOT EXISTS "{index}" ON "{table}" ("company_id");')
    return "\n".join(statements)


async def upgrade(db: BaseDBAsyncClient) -> str:
    return (
        _add_company_columns_sql()
        + """

UPDATE "buildings" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "units" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "incidents" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "tasks" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "inspections" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "reports" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "communications" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "user_condominiums" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "audit_logs" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "ai_requests" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "notification_logs" target
SET "company_id" = source."company_id"
FROM "condominiums" source
WHERE target."condominium_id" = source."id" AND target."company_id" IS NULL;

UPDATE "incident_events" target
SET "company_id" = source."company_id"
FROM "incidents" source
WHERE target."incident_id" = source."id" AND target."company_id" IS NULL;

UPDATE "task_checklists" target
SET "company_id" = source."company_id"
FROM "tasks" source
WHERE target."task_id" = source."id" AND target."company_id" IS NULL;

UPDATE "inspection_answers" target
SET "company_id" = source."company_id"
FROM "inspections" source
WHERE target."inspection_id" = source."id" AND target."company_id" IS NULL;

UPDATE "report_versions" target
SET "company_id" = source."company_id"
FROM "reports" source
WHERE target."report_id" = source."id" AND target."company_id" IS NULL;

UPDATE "communication_recipients" target
SET "company_id" = source."company_id"
FROM "communications" source
WHERE target."communication_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "incidents" source
WHERE target."incident_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "tasks" source
WHERE target."task_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "inspections" source
WHERE target."inspection_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "reports" source
WHERE target."report_id" = source."id" AND target."company_id" IS NULL;

UPDATE "attachments" target
SET "company_id" = source."company_id"
FROM "communications" source
WHERE target."communication_id" = source."id" AND target."company_id" IS NULL;

UPDATE "notification_logs" target
SET "company_id" = source."company_id"
FROM "communications" source
WHERE target."communication_id" = source."id" AND target."company_id" IS NULL;

UPDATE "audit_logs" target
SET "company_id" = source."company_id"
FROM "users" source
WHERE target."user_id" = source."id" AND target."company_id" IS NULL;

UPDATE "ai_requests" target
SET "company_id" = source."company_id"
FROM "users" source
WHERE target."requested_by_id" = source."id" AND target."company_id" IS NULL;

UPDATE "notification_logs" target
SET "company_id" = source."company_id"
FROM "users" source
WHERE target."user_id" = source."id" AND target."company_id" IS NULL;
"""
    )


async def downgrade(db: BaseDBAsyncClient) -> str:
    statements: list[str] = []
    for table in TENANT_TABLES:
        statements.append(f'DROP INDEX IF EXISTS "idx_{table}_company_id";')
        statements.append(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{table}_company_id_fkey";')
        statements.append(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "company_id";')
    return "\n".join(statements)
