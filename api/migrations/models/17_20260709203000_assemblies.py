from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "assemblies" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "title" VARCHAR(180) NOT NULL,
            "description" TEXT,
            "assembly_type" VARCHAR(40) NOT NULL DEFAULT 'ordinary',
            "status" VARCHAR(40) NOT NULL DEFAULT 'scheduled',
            "scheduled_date" DATE NOT NULL,
            "scheduled_start_time" TIME,
            "estimated_duration_minutes" INT,
            "location" VARCHAR(180),
            "modality" VARCHAR(40) NOT NULL DEFAULT 'presential',
            "quorum_required" INT,
            "attendees" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "agenda_items" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "conclusions" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "event_id" UUID REFERENCES "planned_operational_events" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_assemblies_company" ON "assemblies" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_assemblies_cond_status" ON "assemblies" ("condominium_id", "status");
        CREATE INDEX IF NOT EXISTS "idx_assemblies_date" ON "assemblies" ("scheduled_date");
        CREATE INDEX IF NOT EXISTS "idx_assemblies_event" ON "assemblies" ("event_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "assemblies";
    """
