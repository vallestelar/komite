from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
ALTER TABLE "support_tickets" ADD COLUMN IF NOT EXISTS "condominium_id" UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'support_tickets_condominium_id_fkey'
    ) THEN
        ALTER TABLE "support_tickets"
            ADD CONSTRAINT "support_tickets_condominium_id_fkey"
            FOREIGN KEY ("condominium_id") REFERENCES "condominiums" ("id")
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS "idx_support_ti_condomi_0f4b5f" ON "support_tickets" ("condominium_id");

UPDATE "support_tickets" ticket
SET "condominium_id" = condominium."id"
FROM "condominiums" condominium
WHERE ticket."condominium_id" IS NULL
  AND ticket."company_id" = condominium."company_id"
  AND (
      ticket."metadata"->>'condominium_id' = condominium."id"::text
      OR ticket."metadata"->>'condominium_name' = condominium."name"
      OR ticket."metadata"->>'condominium' = condominium."name"
  );
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
ALTER TABLE "support_tickets" DROP CONSTRAINT IF EXISTS "support_tickets_condominium_id_fkey";
DROP INDEX IF EXISTS "idx_support_ti_condomi_0f4b5f";
ALTER TABLE "support_tickets" DROP COLUMN IF EXISTS "condominium_id";
"""
