from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "units" ALTER COLUMN "allocation_identifier" TYPE TEXT;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "units" ALTER COLUMN "allocation_identifier" TYPE VARCHAR(80);
    """
