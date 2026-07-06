from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "committee_members" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "position" VARCHAR(80) NOT NULL,
            "full_name" VARCHAR(150) NOT NULL,
            "email" VARCHAR(255),
            "phone" VARCHAR(40),
            "start_date" DATE,
            "end_date" DATE,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "receives_notifications" BOOL NOT NULL DEFAULT True,
            "display_order" INT NOT NULL DEFAULT 0,
            "notes" TEXT,
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "unit_contact_id" UUID REFERENCES "unit_contacts" ("id") ON DELETE SET NULL,
            "unit_id" UUID REFERENCES "units" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_committee_company_2fc7d9" ON "committee_members" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_committee_condomi_3ab872" ON "committee_members" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_committee_user_7e6472" ON "committee_members" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_committee_contact_34b501" ON "committee_members" ("unit_contact_id");
        CREATE INDEX IF NOT EXISTS "idx_committee_unit_80b2ab" ON "committee_members" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_committee_position_537a17" ON "committee_members" ("position");
        CREATE INDEX IF NOT EXISTS "idx_committee_status_42daba" ON "committee_members" ("status");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "committee_members";
    """
