from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "inspection_templates" ADD COLUMN IF NOT EXISTS "description" TEXT;
        ALTER TABLE "inspection_templates" ADD COLUMN IF NOT EXISTS "template_type" VARCHAR(80) NOT NULL DEFAULT 'inspection';
        ALTER TABLE "inspection_templates" ADD COLUMN IF NOT EXISTS "version" INT NOT NULL DEFAULT 1;
        ALTER TABLE "inspection_templates" ADD COLUMN IF NOT EXISTS "status" VARCHAR(30) NOT NULL DEFAULT 'active';
        ALTER TABLE "inspection_templates" ADD COLUMN IF NOT EXISTS "source_file_name" VARCHAR(255);
        CREATE INDEX IF NOT EXISTS "idx_inspection_templates_template_type" ON "inspection_templates" ("template_type");
        CREATE INDEX IF NOT EXISTS "idx_inspection_templates_status" ON "inspection_templates" ("status");

        CREATE TABLE IF NOT EXISTS "inspection_template_sections" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(150) NOT NULL,
            "description" TEXT,
            "display_order" INT NOT NULL DEFAULT 0,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "template_id" UUID NOT NULL REFERENCES "inspection_templates" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_template_sections_company" ON "inspection_template_sections" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_template_sections_template" ON "inspection_template_sections" ("template_id");
        CREATE INDEX IF NOT EXISTS "idx_template_sections_status" ON "inspection_template_sections" ("status");
        CREATE INDEX IF NOT EXISTS "idx_template_sections_order" ON "inspection_template_sections" ("display_order");

        CREATE TABLE IF NOT EXISTS "inspection_template_items" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "asset_name" VARCHAR(180),
            "task_name" VARCHAR(255) NOT NULL,
            "instructions" TEXT,
            "periodicity" VARCHAR(80),
            "planned_months" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "requires_evidence" BOOL NOT NULL DEFAULT False,
            "default_responsible_profile" VARCHAR(60),
            "default_duration_minutes" INT,
            "display_order" INT NOT NULL DEFAULT 0,
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "template_id" UUID NOT NULL REFERENCES "inspection_templates" ("id") ON DELETE CASCADE,
            "section_id" UUID REFERENCES "inspection_template_sections" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_template_items_company" ON "inspection_template_items" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_template_items_template" ON "inspection_template_items" ("template_id");
        CREATE INDEX IF NOT EXISTS "idx_template_items_section" ON "inspection_template_items" ("section_id");
        CREATE INDEX IF NOT EXISTS "idx_template_items_periodicity" ON "inspection_template_items" ("periodicity");
        CREATE INDEX IF NOT EXISTS "idx_template_items_status" ON "inspection_template_items" ("status");
        CREATE INDEX IF NOT EXISTS "idx_template_items_order" ON "inspection_template_items" ("display_order");

        CREATE TABLE IF NOT EXISTS "condominium_inspection_templates" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(150) NOT NULL,
            "version" INT NOT NULL DEFAULT 1,
            "status" VARCHAR(30) NOT NULL DEFAULT 'draft',
            "effective_from" DATE,
            "effective_to" DATE,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "base_template_id" UUID REFERENCES "inspection_templates" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_company" ON "condominium_inspection_templates" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_condominium" ON "condominium_inspection_templates" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_base" ON "condominium_inspection_templates" ("base_template_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_status" ON "condominium_inspection_templates" ("status");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_effective" ON "condominium_inspection_templates" ("effective_from");

        CREATE TABLE IF NOT EXISTS "condominium_inspection_items" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "section_name" VARCHAR(150),
            "asset_name" VARCHAR(180),
            "task_name" VARCHAR(255) NOT NULL,
            "instructions" TEXT,
            "periodicity" VARCHAR(80),
            "planned_months" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "provider_id" UUID,
            "estimated_duration_minutes" INT,
            "priority" VARCHAR(30) NOT NULL DEFAULT 'medium',
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "condominium_template_id" UUID NOT NULL REFERENCES "condominium_inspection_templates" ("id") ON DELETE CASCADE,
            "base_item_id" UUID REFERENCES "inspection_template_items" ("id") ON DELETE SET NULL,
            "responsible_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "responsible_profile" VARCHAR(60)
        );
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_company" ON "condominium_inspection_items" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_condominium" ON "condominium_inspection_items" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_template" ON "condominium_inspection_items" ("condominium_template_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_base" ON "condominium_inspection_items" ("base_item_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_responsible" ON "condominium_inspection_items" ("responsible_user_id");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_priority" ON "condominium_inspection_items" ("priority");
        CREATE INDEX IF NOT EXISTS "idx_cond_ins_items_status" ON "condominium_inspection_items" ("status");

        CREATE TABLE IF NOT EXISTS "operational_work_calendars" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(150) NOT NULL,
            "calendar_type" VARCHAR(40) NOT NULL DEFAULT 'condominium',
            "working_days" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "default_start_time" TIME,
            "default_end_time" TIME,
            "timezone" VARCHAR(80) NOT NULL DEFAULT 'America/Santiago',
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "effective_from" DATE,
            "effective_to" DATE,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "base_calendar_id" UUID REFERENCES "operational_work_calendars" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_work_calendars_company" ON "operational_work_calendars" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_work_calendars_condominium" ON "operational_work_calendars" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_work_calendars_base" ON "operational_work_calendars" ("base_calendar_id");
        CREATE INDEX IF NOT EXISTS "idx_work_calendars_type" ON "operational_work_calendars" ("calendar_type");
        CREATE INDEX IF NOT EXISTS "idx_work_calendars_status" ON "operational_work_calendars" ("status");

        CREATE TABLE IF NOT EXISTS "operational_calendar_exceptions" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "exception_date" DATE NOT NULL,
            "exception_type" VARCHAR(40) NOT NULL,
            "start_time" TIME,
            "end_time" TIME,
            "reason" VARCHAR(255),
            "source" VARCHAR(40) NOT NULL DEFAULT 'condominium_override',
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "calendar_id" UUID NOT NULL REFERENCES "operational_work_calendars" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_company" ON "operational_calendar_exceptions" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_condominium" ON "operational_calendar_exceptions" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_calendar" ON "operational_calendar_exceptions" ("calendar_id");
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_date" ON "operational_calendar_exceptions" ("exception_date");
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_type" ON "operational_calendar_exceptions" ("exception_type");
        CREATE INDEX IF NOT EXISTS "idx_calendar_exceptions_source" ON "operational_calendar_exceptions" ("source");

        CREATE TABLE IF NOT EXISTS "planned_operational_events" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "title" VARCHAR(180) NOT NULL,
            "description" TEXT,
            "planned_date" DATE NOT NULL,
            "planned_start_time" TIME,
            "planned_end_time" TIME,
            "assigned_profile" VARCHAR(60),
            "priority" VARCHAR(30) NOT NULL DEFAULT 'medium',
            "status" VARCHAR(40) NOT NULL DEFAULT 'pending',
            "source_type" VARCHAR(60),
            "source_id" UUID,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "condominium_template_item_id" UUID REFERENCES "condominium_inspection_items" ("id") ON DELETE SET NULL,
            "calendar_id" UUID REFERENCES "operational_work_calendars" ("id") ON DELETE SET NULL,
            "assigned_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_planned_events_company" ON "planned_operational_events" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_cond_status" ON "planned_operational_events" ("condominium_id", "status");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_item" ON "planned_operational_events" ("condominium_template_item_id");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_calendar" ON "planned_operational_events" ("calendar_id");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_assigned" ON "planned_operational_events" ("assigned_user_id");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_date" ON "planned_operational_events" ("planned_date");
        CREATE INDEX IF NOT EXISTS "idx_planned_events_priority" ON "planned_operational_events" ("priority");

        CREATE TABLE IF NOT EXISTS "operational_event_executions" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "executed_at" TIMESTAMPTZ,
            "result" VARCHAR(60) NOT NULL DEFAULT 'pending',
            "comments" TEXT,
            "requires_follow_up" BOOL NOT NULL DEFAULT False,
            "validation_status" VARCHAR(40) NOT NULL DEFAULT 'not_validated',
            "validated_at" TIMESTAMPTZ,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "event_id" UUID NOT NULL REFERENCES "planned_operational_events" ("id") ON DELETE CASCADE,
            "executed_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "related_incident_id" UUID REFERENCES "incidents" ("id") ON DELETE SET NULL,
            "related_ticket_id" UUID REFERENCES "support_tickets" ("id") ON DELETE SET NULL,
            "validated_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_event_exec_company" ON "operational_event_executions" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_event_exec_event" ON "operational_event_executions" ("event_id");
        CREATE INDEX IF NOT EXISTS "idx_event_exec_user" ON "operational_event_executions" ("executed_by_user_id");
        CREATE INDEX IF NOT EXISTS "idx_event_exec_result" ON "operational_event_executions" ("result");
        CREATE INDEX IF NOT EXISTS "idx_event_exec_validation" ON "operational_event_executions" ("validation_status");
        CREATE INDEX IF NOT EXISTS "idx_event_exec_at" ON "operational_event_executions" ("executed_at");

        CREATE TABLE IF NOT EXISTS "operational_event_evidence" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "evidence_type" VARCHAR(40) NOT NULL DEFAULT 'attachment',
            "description" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "event_id" UUID NOT NULL REFERENCES "planned_operational_events" ("id") ON DELETE CASCADE,
            "execution_id" UUID REFERENCES "operational_event_executions" ("id") ON DELETE CASCADE,
            "attachment_id" UUID REFERENCES "attachments" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_event_evidence_company" ON "operational_event_evidence" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_event_evidence_event" ON "operational_event_evidence" ("event_id");
        CREATE INDEX IF NOT EXISTS "idx_event_evidence_execution" ON "operational_event_evidence" ("execution_id");
        CREATE INDEX IF NOT EXISTS "idx_event_evidence_attachment" ON "operational_event_evidence" ("attachment_id");
        CREATE INDEX IF NOT EXISTS "idx_event_evidence_type" ON "operational_event_evidence" ("evidence_type");

        CREATE TABLE IF NOT EXISTS "operational_reschedule_logs" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "previous_date" DATE,
            "new_date" DATE,
            "reason" VARCHAR(255),
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "event_id" UUID NOT NULL REFERENCES "planned_operational_events" ("id") ON DELETE CASCADE,
            "previous_assigned_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "new_assigned_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "requested_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
            "approved_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_company" ON "operational_reschedule_logs" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_event" ON "operational_reschedule_logs" ("event_id");
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_prev_date" ON "operational_reschedule_logs" ("previous_date");
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_new_date" ON "operational_reschedule_logs" ("new_date");
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_requested" ON "operational_reschedule_logs" ("requested_by_user_id");
        CREATE INDEX IF NOT EXISTS "idx_reschedule_logs_approved" ON "operational_reschedule_logs" ("approved_by_user_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "operational_reschedule_logs";
        DROP TABLE IF EXISTS "operational_event_evidence";
        DROP TABLE IF EXISTS "operational_event_executions";
        DROP TABLE IF EXISTS "planned_operational_events";
        DROP TABLE IF EXISTS "operational_calendar_exceptions";
        DROP TABLE IF EXISTS "operational_work_calendars";
        DROP TABLE IF EXISTS "condominium_inspection_items";
        DROP TABLE IF EXISTS "condominium_inspection_templates";
        DROP TABLE IF EXISTS "inspection_template_items";
        DROP TABLE IF EXISTS "inspection_template_sections";
        DROP INDEX IF EXISTS "idx_inspection_templates_status";
        DROP INDEX IF EXISTS "idx_inspection_templates_template_type";
        ALTER TABLE "inspection_templates" DROP COLUMN IF EXISTS "source_file_name";
        ALTER TABLE "inspection_templates" DROP COLUMN IF EXISTS "status";
        ALTER TABLE "inspection_templates" DROP COLUMN IF EXISTS "version";
        ALTER TABLE "inspection_templates" DROP COLUMN IF EXISTS "template_type";
        ALTER TABLE "inspection_templates" DROP COLUMN IF EXISTS "description";
    """
