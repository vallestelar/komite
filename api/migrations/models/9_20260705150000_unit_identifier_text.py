from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "units" ALTER COLUMN "identifier" TYPE TEXT;
        ALTER TABLE "units" ALTER COLUMN "external_code" TYPE TEXT;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "units" ALTER COLUMN "external_code" TYPE VARCHAR(80);
        ALTER TABLE "units" ALTER COLUMN "identifier" TYPE VARCHAR(80);
    """
