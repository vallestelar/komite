from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "banks" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(120) NOT NULL UNIQUE,
    "code" VARCHAR(40) UNIQUE,
    "country" VARCHAR(80) NOT NULL DEFAULT 'Chile',
    "website" VARCHAR(255),
    "status" VARCHAR(30) NOT NULL DEFAULT 'active',
    "metadata" JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_banks_name_64d2bd" ON "banks" ("name");
CREATE INDEX IF NOT EXISTS "idx_banks_code_7fdad9" ON "banks" ("code");
CREATE INDEX IF NOT EXISTS "idx_banks_status_f2d811" ON "banks" ("status");
CREATE TABLE IF NOT EXISTS "support_tickets" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "id" UUID NOT NULL PRIMARY KEY,
    "requester_name" VARCHAR(150),
    "requester_email" VARCHAR(255),
    "subject" VARCHAR(180) NOT NULL,
    "description" TEXT,
    "category" VARCHAR(80) NOT NULL DEFAULT 'general',
    "priority" VARCHAR(30) NOT NULL DEFAULT 'medium',
    "status" VARCHAR(40) NOT NULL DEFAULT 'open',
    "due_date" DATE,
    "resolved_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
    "created_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "assigned_to_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_support_ti_company_1fd9d0" ON "support_tickets" ("company_id", "status");
CREATE INDEX IF NOT EXISTS "idx_support_ti_assigne_2b3cc6" ON "support_tickets" ("assigned_to_id");
CREATE INDEX IF NOT EXISTS "idx_support_ti_priorit_2c1101" ON "support_tickets" ("priority");
CREATE INDEX IF NOT EXISTS "idx_support_ti_due_dat_470c7f" ON "support_tickets" ("due_date");
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "support_tickets";
        DROP TABLE IF EXISTS "banks";
"""
