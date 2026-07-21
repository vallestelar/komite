from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "signature_assets" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(150) NOT NULL,
            "signer_name" VARCHAR(150) NOT NULL,
            "signer_document" VARCHAR(40),
            "signer_position" VARCHAR(120),
            "storage_key" VARCHAR(500),
            "content_type" VARCHAR(80),
            "size_bytes" INT,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS "idx_signature_assets_company_id" ON "signature_assets" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_assets_condominium_id" ON "signature_assets" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_assets_status" ON "signature_assets" ("status");

        CREATE TABLE IF NOT EXISTS "signature_permissions" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "can_use" BOOLEAN NOT NULL DEFAULT TRUE,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "signature_id" UUID NOT NULL REFERENCES "signature_assets" ("id") ON DELETE CASCADE,
            "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_signature_permissions_sig_user_condo" UNIQUE ("signature_id", "user_id", "condominium_id")
        );

        CREATE INDEX IF NOT EXISTS "idx_signature_permissions_company_id" ON "signature_permissions" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_permissions_condominium_id" ON "signature_permissions" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_permissions_signature_id" ON "signature_permissions" ("signature_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_permissions_user_id" ON "signature_permissions" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_signature_permissions_status" ON "signature_permissions" ("status");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "signature_permissions";
        DROP TABLE IF EXISTS "signature_assets";
    """
