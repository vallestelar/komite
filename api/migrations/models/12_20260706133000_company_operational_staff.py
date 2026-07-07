from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "condominium_operational_staff"
            ALTER COLUMN "condominium_id" DROP NOT NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DELETE FROM "condominium_operational_staff" WHERE "condominium_id" IS NULL;
        ALTER TABLE "condominium_operational_staff"
            ALTER COLUMN "condominium_id" SET NOT NULL;
    """
