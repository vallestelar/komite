from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "accounting_supplier_categories" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(120),
            "updated_by" VARCHAR(120),
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(120) NOT NULL,
            "code" VARCHAR(80),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "display_order" INT NOT NULL DEFAULT 0,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_acc_supplier_categories_company_code" UNIQUE ("company_id", "code")
        );

        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_categories_company_id" ON "accounting_supplier_categories" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_categories_name" ON "accounting_supplier_categories" ("name");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_categories_code" ON "accounting_supplier_categories" ("code");
        CREATE INDEX IF NOT EXISTS "idx_acc_supplier_categories_status" ON "accounting_supplier_categories" ("status");

        ALTER TABLE "accounting_suppliers"
            ADD COLUMN IF NOT EXISTS "supplier_category_id" UUID REFERENCES "accounting_supplier_categories" ("id") ON DELETE SET NULL;

        CREATE INDEX IF NOT EXISTS "idx_accounting_suppliers_supplier_category_id" ON "accounting_suppliers" ("supplier_category_id");

        INSERT INTO "accounting_supplier_categories" (
            "id",
            "created_at",
            "updated_at",
            "company_id",
            "name",
            "code",
            "status",
            "display_order",
            "metadata"
        )
        SELECT
            (
                substr(md5(c."id"::text || seed."code"), 1, 8) || '-' ||
                substr(md5(c."id"::text || seed."code"), 9, 4) || '-' ||
                substr(md5(c."id"::text || seed."code"), 13, 4) || '-' ||
                substr(md5(c."id"::text || seed."code"), 17, 4) || '-' ||
                substr(md5(c."id"::text || seed."code"), 21, 12)
            )::uuid,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            c."id",
            seed."name",
            seed."code",
            'active',
            seed."display_order",
            jsonb_build_object('default_category', true)
        FROM "companies" c
        CROSS JOIN (
            VALUES
                ('maintenance', 'Mantención', 10),
                ('utilities', 'Servicios básicos', 20),
                ('cleaning', 'Aseo y limpieza', 30),
                ('security', 'Seguridad', 40),
                ('gardening', 'Jardinería', 50),
                ('common_areas', 'Piscina y espacios comunes', 60),
                ('elevators', 'Ascensores', 70),
                ('pest_control', 'Control de plagas', 80),
                ('administration', 'Administración', 90),
                ('repairs', 'Reparaciones y obras', 100),
                ('supplies', 'Suministros', 110),
                ('technology', 'Tecnología', 120),
                ('insurance', 'Seguros', 130),
                ('professional_fees', 'Honorarios profesionales', 140),
                ('other', 'Otros', 999)
        ) AS seed("code", "name", "display_order")
        ON CONFLICT ("company_id", "code") DO NOTHING;

        UPDATE "accounting_suppliers" s
        SET "supplier_category_id" = cat."id"
        FROM "accounting_supplier_categories" cat
        WHERE cat."company_id" = s."company_id"
          AND s."supplier_category_id" IS NULL
          AND (
            lower(regexp_replace(coalesce(s."category", ''), '[^a-zA-Z0-9]+', '_', 'g')) = cat."code"
            OR lower(coalesce(s."category", '')) = lower(cat."name")
          );
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "accounting_suppliers" DROP COLUMN IF EXISTS "supplier_category_id";
        DROP TABLE IF EXISTS "accounting_supplier_categories";
    """
