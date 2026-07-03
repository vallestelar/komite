from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
UPDATE "users"
SET "company_profile" = CASE
    WHEN "company_profile" IN ('project_manager', 'ejecutivo') THEN "company_profile"
    WHEN "company_profile" IN ('supervisor', 'conserje') THEN 'ejecutivo'
    ELSE "company_profile"
END;

DROP INDEX IF EXISTS "idx_users_global_role";
ALTER TABLE "users" DROP COLUMN IF EXISTS "global_role";
CREATE INDEX IF NOT EXISTS "idx_users_company_profile" ON "users" ("company_profile");

ALTER TABLE "user_condominiums" DROP CONSTRAINT IF EXISTS "uid_user_condom_user_id_324e86";
ALTER TABLE "user_condominiums" ALTER COLUMN "condominium_id" DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_user_condom_all_without_unit'
    ) THEN
        ALTER TABLE "user_condominiums"
            ADD CONSTRAINT "chk_user_condom_all_without_unit"
            CHECK ("condominium_id" IS NOT NULL OR "unit_id" IS NULL);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_condom_all_company_role"
    ON "user_condominiums" ("user_id", "company_id", "role_id")
    WHERE "condominium_id" IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_condom_specific_role_unit"
    ON "user_condominiums" ("user_id", "condominium_id", "role_id", COALESCE("unit_id", '00000000-0000-0000-0000-000000000000'::uuid))
    WHERE "condominium_id" IS NOT NULL;
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
DROP INDEX IF EXISTS "uid_user_condom_specific_role_unit";
DROP INDEX IF EXISTS "uid_user_condom_all_company_role";
ALTER TABLE "user_condominiums" DROP CONSTRAINT IF EXISTS "chk_user_condom_all_without_unit";
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "global_role" VARCHAR(60) DEFAULT 'user';
UPDATE "users" SET "global_role" = 'user' WHERE "global_role" IS NULL;
ALTER TABLE "users" ALTER COLUMN "global_role" SET NOT NULL;
CREATE INDEX IF NOT EXISTS "idx_users_global_role" ON "users" ("global_role");
"""
