from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "planned_operational_events"
        ADD COLUMN IF NOT EXISTS "event_type" VARCHAR(40) NOT NULL DEFAULT 'task';

        UPDATE "planned_operational_events"
        SET "event_type" = CASE
            WHEN "source_type" = 'unplanned_incident' THEN 'incident'
            WHEN "source_type" = 'inspection_template' THEN 'inspection'
            WHEN "source_type" = 'maintenance_template' THEN 'maintenance'
            ELSE 'task'
        END
        WHERE "event_type" IS NULL OR "event_type" = 'task';

        CREATE INDEX IF NOT EXISTS "idx_planned_op_condom_event_type"
        ON "planned_operational_events" ("condominium_id", "event_type");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_planned_op_condom_event_type";
        ALTER TABLE "planned_operational_events"
        DROP COLUMN IF EXISTS "event_type";
    """
