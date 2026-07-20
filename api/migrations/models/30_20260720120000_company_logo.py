from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "companies" ADD "logo_url" VARCHAR(500);
        ALTER TABLE "companies" ADD "logo_storage_key" VARCHAR(500);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "companies" DROP COLUMN "logo_url";
        ALTER TABLE "companies" DROP COLUMN "logo_storage_key";
    """
