from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "organization_position" VARCHAR(120);
        CREATE INDEX IF NOT EXISTS "idx_users_org_position" ON "users" ("organization_position");

        CREATE TABLE IF NOT EXISTS "condominium_operational_staff" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "portal_profile" VARCHAR(60) NOT NULL,
            "responsibility" VARCHAR(120),
            "is_primary" BOOL NOT NULL DEFAULT False,
            "start_date" DATE,
            "end_date" DATE,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL,
            "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_cond_staff_cond_user_profile" UNIQUE ("condominium_id", "user_id", "portal_profile")
        );
        CREATE INDEX IF NOT EXISTS "idx_cond_staff_company" ON "condominium_operational_staff" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_staff_condominium" ON "condominium_operational_staff" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_staff_user" ON "condominium_operational_staff" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_staff_profile" ON "condominium_operational_staff" ("portal_profile");
        CREATE INDEX IF NOT EXISTS "idx_cond_staff_status" ON "condominium_operational_staff" ("status");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "condominium_operational_staff";
        DROP INDEX IF EXISTS "idx_users_org_position";
        ALTER TABLE "users" DROP COLUMN IF EXISTS "organization_position";
    """
