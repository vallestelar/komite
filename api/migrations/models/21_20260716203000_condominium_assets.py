from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "condominium_assets" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(140) NOT NULL,
            "asset_type" VARCHAR(50) NOT NULL DEFAULT 'other',
            "location" VARCHAR(160),
            "brand" VARCHAR(100),
            "model" VARCHAR(100),
            "serial_number" VARCHAR(100),
            "provider" VARCHAR(160),
            "installation_date" DATE,
            "requires_maintenance" BOOL NOT NULL DEFAULT True,
            "maintenance_frequency" VARCHAR(80),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS "idx_cond_asset_company_id" ON "condominium_assets" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_asset_condominium_id" ON "condominium_assets" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_asset_asset_type" ON "condominium_assets" ("asset_type");
        CREATE INDEX IF NOT EXISTS "idx_cond_asset_status" ON "condominium_assets" ("status");
        CREATE INDEX IF NOT EXISTS "idx_cond_asset_serial_number" ON "condominium_assets" ("serial_number");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "condominium_assets";
    """
