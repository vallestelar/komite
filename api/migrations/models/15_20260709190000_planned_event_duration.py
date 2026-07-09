from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "planned_operational_events"
        ADD COLUMN IF NOT EXISTS "estimated_duration_minutes" INT;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "planned_operational_events"
        DROP COLUMN IF EXISTS "estimated_duration_minutes";
    """
