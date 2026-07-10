from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "inspection_template_items"
        ADD COLUMN IF NOT EXISTS "event_type" VARCHAR(40) NOT NULL DEFAULT 'maintenance';

        ALTER TABLE "condominium_inspection_items"
        ADD COLUMN IF NOT EXISTS "event_type" VARCHAR(40) NOT NULL DEFAULT 'maintenance';

        CREATE INDEX IF NOT EXISTS "idx_template_items_event_type"
        ON "inspection_template_items" ("event_type");

        CREATE INDEX IF NOT EXISTS "idx_cond_items_event_type"
        ON "condominium_inspection_items" ("event_type");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_cond_items_event_type";
        DROP INDEX IF EXISTS "idx_template_items_event_type";
        ALTER TABLE "condominium_inspection_items" DROP COLUMN IF EXISTS "event_type";
        ALTER TABLE "inspection_template_items" DROP COLUMN IF EXISTS "event_type";
    """
