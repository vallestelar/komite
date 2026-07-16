from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "common_areas" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(120) NOT NULL,
            "area_type" VARCHAR(40) NOT NULL DEFAULT 'other',
            "location" VARCHAR(160),
            "capacity" INT,
            "requires_reservation" BOOL NOT NULL DEFAULT False,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS "idx_common_area_company_id" ON "common_areas" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_common_area_condominium_id" ON "common_areas" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_common_area_area_type" ON "common_areas" ("area_type");
        CREATE INDEX IF NOT EXISTS "idx_common_area_status" ON "common_areas" ("status");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "common_areas";
    """
