from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "accounting_incomes" ADD COLUMN IF NOT EXISTS "bank_id" UUID REFERENCES "banks" ("id") ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_bank" ON "accounting_incomes" ("bank_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_accounting_incomes_bank";
        ALTER TABLE "accounting_incomes" DROP COLUMN IF EXISTS "bank_id";
    """
