from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "unit_annexes" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "annex_type" VARCHAR(40) NOT NULL DEFAULT 'parking',
            "identifier" VARCHAR(80) NOT NULL,
            "description" VARCHAR(255),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "unit_id" UUID NOT NULL REFERENCES "units" ("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS "idx_unit_annex_company_id" ON "unit_annexes" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_annex_condominium_id" ON "unit_annexes" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_annex_unit_id" ON "unit_annexes" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_annex_annex_type" ON "unit_annexes" ("annex_type");
        CREATE INDEX IF NOT EXISTS "idx_unit_annex_status" ON "unit_annexes" ("status");

        CREATE TABLE IF NOT EXISTS "unit_pets" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(120) NOT NULL,
            "species" VARCHAR(40) NOT NULL DEFAULT 'dog',
            "breed" VARCHAR(120),
            "color" VARCHAR(80),
            "chip_number" VARCHAR(80),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "unit_id" UUID NOT NULL REFERENCES "units" ("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS "idx_unit_pet_company_id" ON "unit_pets" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_pet_condominium_id" ON "unit_pets" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_pet_unit_id" ON "unit_pets" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_pet_species" ON "unit_pets" ("species");
        CREATE INDEX IF NOT EXISTS "idx_unit_pet_status" ON "unit_pets" ("status");
        CREATE INDEX IF NOT EXISTS "idx_unit_pet_chip_number" ON "unit_pets" ("chip_number");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "unit_pets";
        DROP TABLE IF EXISTS "unit_annexes";
    """
