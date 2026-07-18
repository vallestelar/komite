from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "accounting_supplier_condominiums" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "supplier_id" UUID NOT NULL REFERENCES "accounting_suppliers" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_accounting_supplier_condominiums_supplier_condo" UNIQUE ("supplier_id", "condominium_id")
        );

        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_cond_company_id" ON "accounting_supplier_condominiums" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_cond_supplier_id" ON "accounting_supplier_condominiums" ("supplier_id");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_cond_condominium_id" ON "accounting_supplier_condominiums" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_cond_status" ON "accounting_supplier_condominiums" ("status");

        INSERT INTO "accounting_supplier_condominiums" (
            "id",
            "created_at",
            "updated_at",
            "company_id",
            "supplier_id",
            "condominium_id",
            "status",
            "notes",
            "metadata"
        )
        SELECT
            (
                substr(md5(s."id"::text || s."condominium_id"::text), 1, 8) || '-' ||
                substr(md5(s."id"::text || s."condominium_id"::text), 9, 4) || '-' ||
                substr(md5(s."id"::text || s."condominium_id"::text), 13, 4) || '-' ||
                substr(md5(s."id"::text || s."condominium_id"::text), 17, 4) || '-' ||
                substr(md5(s."id"::text || s."condominium_id"::text), 21, 12)
            )::uuid,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            COALESCE(s."company_id", c."company_id"),
            s."id",
            s."condominium_id",
            s."status",
            s."notes",
            jsonb_build_object('migrated_from_supplier_condominium_id', true)
        FROM "accounting_suppliers" s
        JOIN "condominiums" c ON c."id" = s."condominium_id"
        WHERE s."condominium_id" IS NOT NULL
        ON CONFLICT ("supplier_id", "condominium_id") DO NOTHING;

        UPDATE "accounting_suppliers"
        SET "company_id" = c."company_id"
        FROM "condominiums" c
        WHERE "accounting_suppliers"."condominium_id" = c."id"
          AND "accounting_suppliers"."company_id" IS NULL;

        UPDATE "accounting_suppliers"
        SET "condominium_id" = NULL
        WHERE "condominium_id" IS NOT NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "accounting_suppliers" s
        SET "condominium_id" = l."condominium_id"
        FROM "accounting_supplier_condominiums" l
        WHERE l."supplier_id" = s."id"
          AND s."condominium_id" IS NULL;

        DROP TABLE IF EXISTS "accounting_supplier_condominiums";
    """
