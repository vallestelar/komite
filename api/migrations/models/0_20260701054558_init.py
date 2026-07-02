from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "companies" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(150) NOT NULL,
    "rut" VARCHAR(30)  UNIQUE,
    "legal_name" VARCHAR(180),
    "email" VARCHAR(255),
    "phone" VARCHAR(40),
    "status" VARCHAR(30) NOT NULL  DEFAULT 'active',
    "metadata" JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_companies_name_1b02af" ON "companies" ("name");
CREATE INDEX IF NOT EXISTS "idx_companies_status_500665" ON "companies" ("status");
CREATE TABLE IF NOT EXISTS "condominiums" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(150) NOT NULL,
    "address" VARCHAR(255),
    "commune" VARCHAR(100),
    "city" VARCHAR(100),
    "region" VARCHAR(100),
    "towers_count" INT NOT NULL  DEFAULT 0,
    "units_count" INT NOT NULL  DEFAULT 0,
    "status" VARCHAR(30) NOT NULL  DEFAULT 'active',
    "communication_rules" JSONB NOT NULL,
    "incident_categories" JSONB NOT NULL,
    "metadata" JSONB NOT NULL,
    "company_id" UUID NOT NULL REFERENCES "companies" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_condominium_company_d8d0b7" ON "condominiums" ("company_id", "name");
CREATE INDEX IF NOT EXISTS "idx_condominium_status_e4d69f" ON "condominiums" ("status");
CREATE TABLE IF NOT EXISTS "buildings" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "floors_count" INT NOT NULL  DEFAULT 0,
    "units_count" INT NOT NULL  DEFAULT 0,
    "metadata" JSONB NOT NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_buildings_condomi_fa3dcc" ON "buildings" ("condominium_id", "name");
CREATE TABLE IF NOT EXISTS "inspection_templates" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "name" VARCHAR(150) NOT NULL,
    "inspection_type" VARCHAR(80) NOT NULL,
    "checklist_schema" JSONB NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "metadata" JSONB NOT NULL,
    "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
    "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_inspection__company_7de207" ON "inspection_templates" ("company_id");
CREATE INDEX IF NOT EXISTS "idx_inspection__condomi_a05606" ON "inspection_templates" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_inspection__inspect_02cd1f" ON "inspection_templates" ("inspection_type");
CREATE INDEX IF NOT EXISTS "idx_inspection__is_acti_1119fa" ON "inspection_templates" ("is_active");
CREATE TABLE IF NOT EXISTS "roles" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "code" VARCHAR(60) NOT NULL UNIQUE,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "permissions" JSONB NOT NULL,
    "is_system" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_roles_code_4f0799" ON "roles" ("code");
CREATE TABLE IF NOT EXISTS "units" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "identifier" VARCHAR(80) NOT NULL,
    "floor" VARCHAR(20),
    "unit_type" VARCHAR(30) NOT NULL  DEFAULT 'apartment',
    "metadata" JSONB NOT NULL,
    "building_id" UUID REFERENCES "buildings" ("id") ON DELETE SET NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_units_condomi_e63fbd" ON "units" ("condominium_id", "identifier");
CREATE INDEX IF NOT EXISTS "idx_units_buildin_53d154" ON "units" ("building_id");
CREATE TABLE IF NOT EXISTS "users" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255),
    "full_name" VARCHAR(150) NOT NULL,
    "phone" VARCHAR(40),
    "status" VARCHAR(30) NOT NULL  DEFAULT 'active',
    "global_role" VARCHAR(60),
    "metadata" JSONB NOT NULL,
    "company_id" UUID REFERENCES "companies" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
CREATE INDEX IF NOT EXISTS "idx_users_company_0463c9" ON "users" ("company_id");
CREATE INDEX IF NOT EXISTS "idx_users_status_941fc1" ON "users" ("status");
CREATE TABLE IF NOT EXISTS "ai_requests" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "provider" VARCHAR(60) NOT NULL,
    "model" VARCHAR(100) NOT NULL,
    "purpose" VARCHAR(80) NOT NULL,
    "input_payload" JSONB NOT NULL,
    "output_payload" JSONB,
    "status" VARCHAR(40) NOT NULL  DEFAULT 'pending',
    "confidence_score" DOUBLE PRECISION,
    "error_message" TEXT,
    "tokens_input" INT,
    "tokens_output" INT,
    "cost_estimate" DECIMAL(12,4),
    "metadata" JSONB NOT NULL,
    "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE SET NULL,
    "requested_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_ai_requests_condomi_7779f5" ON "ai_requests" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_ai_requests_purpose_55706d" ON "ai_requests" ("purpose");
CREATE INDEX IF NOT EXISTS "idx_ai_requests_provide_332331" ON "ai_requests" ("provider", "model");
CREATE INDEX IF NOT EXISTS "idx_ai_requests_status_d92858" ON "ai_requests" ("status");
CREATE INDEX IF NOT EXISTS "idx_ai_requests_created_656340" ON "ai_requests" ("created_at");
CREATE TABLE IF NOT EXISTS "audit_logs" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "action" VARCHAR(100) NOT NULL,
    "entity_type" VARCHAR(80) NOT NULL,
    "entity_id" UUID,
    "previous_state" JSONB,
    "new_state" JSONB,
    "ip_address" VARCHAR(80),
    "user_agent" VARCHAR(255),
    "metadata" JSONB NOT NULL,
    "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE SET NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_audit_logs_condomi_72bed8" ON "audit_logs" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_user_id_f7db5c" ON "audit_logs" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_entity__1b0d2b" ON "audit_logs" ("entity_type", "entity_id");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_action_4eb755" ON "audit_logs" ("action");
CREATE INDEX IF NOT EXISTS "idx_audit_logs_created_bdaee3" ON "audit_logs" ("created_at");
CREATE TABLE IF NOT EXISTS "incidents" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "category" VARCHAR(80) NOT NULL,
    "priority" VARCHAR(30) NOT NULL  DEFAULT 'medium',
    "status" VARCHAR(40) NOT NULL  DEFAULT 'new',
    "original_description" TEXT NOT NULL,
    "ai_description" TEXT,
    "confidence_score" DOUBLE PRECISION,
    "due_date" DATE,
    "closed_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "assigned_to_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "reported_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_incidents_condomi_efa817" ON "incidents" ("condominium_id", "status");
CREATE INDEX IF NOT EXISTS "idx_incidents_categor_9c6eb1" ON "incidents" ("category");
CREATE INDEX IF NOT EXISTS "idx_incidents_priorit_9f9e37" ON "incidents" ("priority");
CREATE INDEX IF NOT EXISTS "idx_incidents_due_dat_295d43" ON "incidents" ("due_date");
CREATE TABLE IF NOT EXISTS "incident_events" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "event_type" VARCHAR(60) NOT NULL,
    "previous_status" VARCHAR(40),
    "new_status" VARCHAR(40),
    "comment" TEXT,
    "metadata" JSONB NOT NULL,
    "incident_id" UUID NOT NULL REFERENCES "incidents" ("id") ON DELETE CASCADE,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_incident_ev_inciden_1ca135" ON "incident_events" ("incident_id");
CREATE INDEX IF NOT EXISTS "idx_incident_ev_event_t_a0e0f7" ON "incident_events" ("event_type");
CREATE INDEX IF NOT EXISTS "idx_incident_ev_created_a92de3" ON "incident_events" ("created_at");
CREATE TABLE IF NOT EXISTS "inspections" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "inspection_type" VARCHAR(80) NOT NULL,
    "status" VARCHAR(40) NOT NULL  DEFAULT 'draft',
    "observations" TEXT,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "signed_at" TIMESTAMPTZ,
    "submitted_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "supervisor_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "template_id" UUID REFERENCES "inspection_templates" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_inspections_condomi_f1501d" ON "inspections" ("condominium_id", "status");
CREATE INDEX IF NOT EXISTS "idx_inspections_supervi_11f8f8" ON "inspections" ("supervisor_id");
CREATE INDEX IF NOT EXISTS "idx_inspections_inspect_108ca6" ON "inspections" ("inspection_type");
CREATE INDEX IF NOT EXISTS "idx_inspections_submitt_d6e748" ON "inspections" ("submitted_at");
CREATE TABLE IF NOT EXISTS "inspection_answers" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "question_key" VARCHAR(100) NOT NULL,
    "question_label" VARCHAR(255) NOT NULL,
    "answer_type" VARCHAR(40) NOT NULL  DEFAULT 'text',
    "value" JSONB NOT NULL,
    "requires_action" BOOL NOT NULL  DEFAULT False,
    "metadata" JSONB NOT NULL,
    "inspection_id" UUID NOT NULL REFERENCES "inspections" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_inspection__inspect_4a1401" ON "inspection_answers" ("inspection_id");
CREATE INDEX IF NOT EXISTS "idx_inspection__questio_e15f87" ON "inspection_answers" ("question_key");
CREATE INDEX IF NOT EXISTS "idx_inspection__require_7cea1a" ON "inspection_answers" ("requires_action");
CREATE TABLE IF NOT EXISTS "tasks" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "title" VARCHAR(180) NOT NULL,
    "description" TEXT,
    "status" VARCHAR(40) NOT NULL  DEFAULT 'pending',
    "priority" VARCHAR(30) NOT NULL  DEFAULT 'medium',
    "due_date" DATE,
    "completed_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "assigned_to_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "created_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "incident_id" UUID REFERENCES "incidents" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_tasks_condomi_71b491" ON "tasks" ("condominium_id", "status");
CREATE INDEX IF NOT EXISTS "idx_tasks_assigne_9c83ae" ON "tasks" ("assigned_to_id");
CREATE INDEX IF NOT EXISTS "idx_tasks_due_dat_89d016" ON "tasks" ("due_date");
CREATE INDEX IF NOT EXISTS "idx_tasks_priorit_236091" ON "tasks" ("priority");
CREATE TABLE IF NOT EXISTS "reports" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "report_type" VARCHAR(60) NOT NULL,
    "title" VARCHAR(180) NOT NULL,
    "status" VARCHAR(40) NOT NULL  DEFAULT 'draft',
    "content" JSONB NOT NULL,
    "approved_at" TIMESTAMPTZ,
    "published_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "approved_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "created_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "incident_id" UUID REFERENCES "incidents" ("id") ON DELETE SET NULL,
    "inspection_id" UUID REFERENCES "inspections" ("id") ON DELETE SET NULL,
    "task_id" UUID REFERENCES "tasks" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_reports_condomi_f5b4be" ON "reports" ("condominium_id", "status");
CREATE INDEX IF NOT EXISTS "idx_reports_report__d2224c" ON "reports" ("report_type");
CREATE INDEX IF NOT EXISTS "idx_reports_publish_8a20b6" ON "reports" ("published_at");
CREATE TABLE IF NOT EXISTS "communications" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "communication_type" VARCHAR(60) NOT NULL,
    "title" VARCHAR(180) NOT NULL,
    "body" TEXT NOT NULL,
    "status" VARCHAR(40) NOT NULL  DEFAULT 'draft',
    "audience" VARCHAR(40) NOT NULL  DEFAULT 'committee',
    "channels" JSONB NOT NULL,
    "scheduled_at" TIMESTAMPTZ,
    "sent_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "approved_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "created_by_user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "report_id" UUID REFERENCES "reports" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_communicati_condomi_762915" ON "communications" ("condominium_id", "status");
CREATE INDEX IF NOT EXISTS "idx_communicati_communi_3ad34a" ON "communications" ("communication_type");
CREATE INDEX IF NOT EXISTS "idx_communicati_audienc_4706b4" ON "communications" ("audience");
CREATE INDEX IF NOT EXISTS "idx_communicati_sent_at_9c9600" ON "communications" ("sent_at");
CREATE TABLE IF NOT EXISTS "attachments" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "file_name" VARCHAR(255) NOT NULL,
    "file_path" VARCHAR(500) NOT NULL,
    "file_type" VARCHAR(80) NOT NULL,
    "mime_type" VARCHAR(120),
    "size_bytes" BIGINT,
    "checksum" VARCHAR(128),
    "metadata" JSONB NOT NULL,
    "communication_id" UUID REFERENCES "communications" ("id") ON DELETE CASCADE,
    "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "incident_id" UUID REFERENCES "incidents" ("id") ON DELETE CASCADE,
    "inspection_id" UUID REFERENCES "inspections" ("id") ON DELETE CASCADE,
    "report_id" UUID REFERENCES "reports" ("id") ON DELETE CASCADE,
    "task_id" UUID REFERENCES "tasks" ("id") ON DELETE CASCADE,
    "uploaded_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_attachments_condomi_c70fdb" ON "attachments" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_attachments_inciden_7e31a5" ON "attachments" ("incident_id");
CREATE INDEX IF NOT EXISTS "idx_attachments_task_id_86e5bd" ON "attachments" ("task_id");
CREATE INDEX IF NOT EXISTS "idx_attachments_inspect_13c8ca" ON "attachments" ("inspection_id");
CREATE INDEX IF NOT EXISTS "idx_attachments_file_ty_662186" ON "attachments" ("file_type");
CREATE TABLE IF NOT EXISTS "communication_recipients" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "recipient_type" VARCHAR(40) NOT NULL  DEFAULT 'user',
    "channel" VARCHAR(40) NOT NULL,
    "destination" VARCHAR(255),
    "delivery_status" VARCHAR(40) NOT NULL  DEFAULT 'pending',
    "delivered_at" TIMESTAMPTZ,
    "read_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "communication_id" UUID NOT NULL REFERENCES "communications" ("id") ON DELETE CASCADE,
    "unit_id" UUID REFERENCES "units" ("id") ON DELETE SET NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_communicati_communi_5302c3" ON "communication_recipients" ("communication_id");
CREATE INDEX IF NOT EXISTS "idx_communicati_user_id_689522" ON "communication_recipients" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_communicati_channel_e97e75" ON "communication_recipients" ("channel");
CREATE INDEX IF NOT EXISTS "idx_communicati_deliver_37e018" ON "communication_recipients" ("delivery_status");
CREATE TABLE IF NOT EXISTS "notification_logs" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "channel" VARCHAR(40) NOT NULL,
    "destination" VARCHAR(255),
    "status" VARCHAR(40) NOT NULL  DEFAULT 'pending',
    "provider_message_id" VARCHAR(120),
    "error_message" TEXT,
    "sent_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "communication_id" UUID REFERENCES "communications" ("id") ON DELETE SET NULL,
    "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE SET NULL,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_notificatio_condomi_7fb789" ON "notification_logs" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_notificatio_communi_9301e3" ON "notification_logs" ("communication_id");
CREATE INDEX IF NOT EXISTS "idx_notificatio_user_id_a388bf" ON "notification_logs" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_notificatio_channel_784ec4" ON "notification_logs" ("channel");
CREATE INDEX IF NOT EXISTS "idx_notificatio_status_ee45b1" ON "notification_logs" ("status");
CREATE INDEX IF NOT EXISTS "idx_notificatio_sent_at_5da039" ON "notification_logs" ("sent_at");
CREATE TABLE IF NOT EXISTS "report_versions" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "version_number" INT NOT NULL,
    "source" VARCHAR(40) NOT NULL  DEFAULT 'human',
    "content" JSONB NOT NULL,
    "notes" TEXT,
    "report_id" UUID NOT NULL REFERENCES "reports" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_report_vers_report__8ea5ed" UNIQUE ("report_id", "version_number")
);
CREATE INDEX IF NOT EXISTS "idx_report_vers_report__8ea5ed" ON "report_versions" ("report_id", "version_number");
CREATE INDEX IF NOT EXISTS "idx_report_vers_source_fc2062" ON "report_versions" ("source");
CREATE TABLE IF NOT EXISTS "task_checklists" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "label" VARCHAR(180) NOT NULL,
    "is_completed" BOOL NOT NULL  DEFAULT False,
    "completed_at" TIMESTAMPTZ,
    "position" INT NOT NULL  DEFAULT 0,
    "completed_by_id" UUID REFERENCES "users" ("id") ON DELETE SET NULL,
    "task_id" UUID NOT NULL REFERENCES "tasks" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_task_checkl_task_id_6c3f2d" ON "task_checklists" ("task_id", "position");
CREATE TABLE IF NOT EXISTS "user_condominiums" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL  DEFAULT 'system',
    "id" UUID NOT NULL  PRIMARY KEY,
    "status" VARCHAR(30) NOT NULL  DEFAULT 'active',
    "receives_notifications" BOOL NOT NULL  DEFAULT True,
    "metadata" JSONB NOT NULL,
    "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
    "role_id" UUID NOT NULL REFERENCES "roles" ("id") ON DELETE RESTRICT,
    "unit_id" UUID REFERENCES "units" ("id") ON DELETE SET NULL,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_condom_user_id_324e86" UNIQUE ("user_id", "condominium_id", "role_id", "unit_id")
);
CREATE INDEX IF NOT EXISTS "idx_user_condom_user_id_adc257" ON "user_condominiums" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_condom_condomi_26ae65" ON "user_condominiums" ("condominium_id");
CREATE INDEX IF NOT EXISTS "idx_user_condom_role_id_4279e1" ON "user_condominiums" ("role_id");
CREATE INDEX IF NOT EXISTS "idx_user_condom_status_5483e1" ON "user_condominiums" ("status");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
