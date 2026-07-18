from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "operational_notifications" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "source_type" VARCHAR(60) NOT NULL DEFAULT 'external_service_order',
            "source_id" VARCHAR(80),
            "title" VARCHAR(180) NOT NULL,
            "summary" TEXT,
            "body" TEXT,
            "draft_body" TEXT,
            "final_body" TEXT,
            "status" VARCHAR(40) NOT NULL DEFAULT 'pending_review',
            "priority" VARCHAR(30) NOT NULL DEFAULT 'medium',
            "send_status" VARCHAR(40) NOT NULL DEFAULT 'not_ready',
            "send_channel" VARCHAR(40) NOT NULL DEFAULT 'mobile_app',
            "mobile_payload" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "validated_at" TIMESTAMPTZ,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "event_id" UUID REFERENCES "planned_operational_events" ("id") ON DELETE SET NULL,
            "external_service_order_id" UUID REFERENCES "external_service_orders" ("id") ON DELETE SET NULL,
            "ai_request_id" UUID REFERENCES "ai_requests" ("id") ON DELETE SET NULL,
            "report_id" UUID REFERENCES "reports" ("id") ON DELETE SET NULL,
            "assigned_to_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "validated_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_company_id" ON "operational_notifications" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_condominium_status" ON "operational_notifications" ("condominium_id", "status");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_event_id" ON "operational_notifications" ("event_id");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_external_order_id" ON "operational_notifications" ("external_service_order_id");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_assigned_status" ON "operational_notifications" ("assigned_to_id", "status");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_validated_by_id" ON "operational_notifications" ("validated_by_id");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_report_id" ON "operational_notifications" ("report_id");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_priority" ON "operational_notifications" ("priority");
        CREATE INDEX IF NOT EXISTS "idx_operational_notifications_send_status" ON "operational_notifications" ("send_status");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "operational_notifications";
    """
