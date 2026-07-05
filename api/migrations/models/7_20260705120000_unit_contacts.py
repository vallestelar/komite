from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "external_code" VARCHAR(80);
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "allocation_number" INT;
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "allocation_identifier" VARCHAR(80);
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "proration_total" NUMERIC(12,6);
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "proration" NUMERIC(12,6);
        ALTER TABLE "units" ADD COLUMN IF NOT EXISTS "assignment_date" DATE;
        CREATE INDEX IF NOT EXISTS "idx_units_condomi_extern_9d4b81" ON "units" ("condominium_id", "external_code");

        ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "document_type" VARCHAR(30);
        ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "document_number" VARCHAR(40);
        ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "address" VARCHAR(255);
        CREATE INDEX IF NOT EXISTS "idx_users_documen_5896c4" ON "users" ("document_number");

        CREATE TABLE IF NOT EXISTS "unit_contacts" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "relationship_type" VARCHAR(40) NOT NULL DEFAULT 'residente',
            "full_name" VARCHAR(150) NOT NULL,
            "email" VARCHAR(255),
            "phone" VARCHAR(40),
            "document_type" VARCHAR(30),
            "document_number" VARCHAR(40),
            "address" VARCHAR(255),
            "is_primary_contact" BOOL NOT NULL DEFAULT False,
            "receives_notifications" BOOL NOT NULL DEFAULT True,
            "start_date" DATE,
            "end_date" DATE,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "unit_id" UUID NOT NULL REFERENCES "units" ("id") ON DELETE CASCADE,
            "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_company_b79a09" ON "unit_contacts" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_condomi_528c7b" ON "unit_contacts" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_unit_id_1a0ac0" ON "unit_contacts" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_user_id_2e0d74" ON "unit_contacts" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_relatio_ef57ce" ON "unit_contacts" ("relationship_type");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_status_349b60" ON "unit_contacts" ("status");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_documen_1b6636" ON "unit_contacts" ("document_number");
        CREATE INDEX IF NOT EXISTS "idx_unit_conta_email_b841b0" ON "unit_contacts" ("email");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "unit_contacts";
        DROP INDEX IF EXISTS "idx_users_documen_5896c4";
        ALTER TABLE "users" DROP COLUMN IF EXISTS "address";
        ALTER TABLE "users" DROP COLUMN IF EXISTS "document_number";
        ALTER TABLE "users" DROP COLUMN IF EXISTS "document_type";
        DROP INDEX IF EXISTS "idx_units_condomi_extern_9d4b81";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "assignment_date";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "proration";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "proration_total";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "allocation_identifier";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "allocation_number";
        ALTER TABLE "units" DROP COLUMN IF EXISTS "external_code";
    """
