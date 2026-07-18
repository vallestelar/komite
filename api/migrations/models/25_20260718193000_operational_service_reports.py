from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "reports"
            ADD COLUMN IF NOT EXISTS "operational_event_id" UUID REFERENCES "planned_operational_events" ("id") ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS "operational_execution_id" UUID REFERENCES "operational_event_executions" ("id") ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS "asset_id" UUID REFERENCES "condominium_assets" ("id") ON DELETE SET NULL;

        CREATE INDEX IF NOT EXISTS "idx_reports_operational_event_id" ON "reports" ("operational_event_id");
        CREATE INDEX IF NOT EXISTS "idx_reports_operational_execution_id" ON "reports" ("operational_execution_id");
        CREATE INDEX IF NOT EXISTS "idx_reports_asset_id" ON "reports" ("asset_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "reports" DROP COLUMN IF EXISTS "asset_id";
        ALTER TABLE "reports" DROP COLUMN IF EXISTS "operational_execution_id";
        ALTER TABLE "reports" DROP COLUMN IF EXISTS "operational_event_id";
    """
