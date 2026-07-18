from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "ai_prompt_templates" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "key" VARCHAR(120) NOT NULL,
            "name" VARCHAR(180) NOT NULL,
            "description" TEXT,
            "purpose" VARCHAR(100) NOT NULL,
            "module" VARCHAR(80) NOT NULL DEFAULT 'general',
            "asset_type" VARCHAR(80),
            "system_template" TEXT NOT NULL,
            "user_template" TEXT NOT NULL,
            "required_variables" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "optional_variables" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "default_model" VARCHAR(120),
            "default_temperature" DOUBLE PRECISION NOT NULL DEFAULT 0.2,
            "default_max_tokens" INT,
            "reasoning_enabled" BOOL NOT NULL DEFAULT FALSE,
            "expects_json" BOOL NOT NULL DEFAULT FALSE,
            "version" INT NOT NULL DEFAULT 1,
            "status" VARCHAR(30) NOT NULL DEFAULT 'draft',
            "is_active" BOOL NOT NULL DEFAULT TRUE,
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_ai_prompt_templates_scope_key_version" UNIQUE ("company_id", "condominium_id", "key", "version")
        );

        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_company_id" ON "ai_prompt_templates" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_condominium_id" ON "ai_prompt_templates" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_key" ON "ai_prompt_templates" ("key");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_purpose" ON "ai_prompt_templates" ("purpose");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_module" ON "ai_prompt_templates" ("module");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_asset_type" ON "ai_prompt_templates" ("asset_type");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_status" ON "ai_prompt_templates" ("status");
        CREATE INDEX IF NOT EXISTS "idx_ai_prompt_templates_is_active" ON "ai_prompt_templates" ("is_active");

        INSERT INTO "ai_prompt_templates" (
            "id", "key", "name", "description", "purpose", "module", "asset_type",
            "system_template", "user_template", "required_variables", "optional_variables",
            "default_model", "default_temperature", "default_max_tokens", "status", "is_active", "metadata"
        )
        VALUES
        (
            '019f76e6-2130-7000-9000-000000000001',
            'elevator_inspection_report',
            'Informe revision ascensor',
            'Borrador profesional para revisiones preventivas o correctivas de ascensores.',
            'elevator_inspection_report',
            'operations',
            'elevator',
            'Eres Komite, asistente operativo para administracion de condominios en Chile. Redactas informes tecnicos claros sobre ascensores para administradores, comites y proveedores. No inventes datos; si falta informacion, marcala como pendiente. Mantén tono profesional, verificable y accionable.',
            'Genera un informe tecnico editable de revision de ascensor.\\n\\nCondominio: {condominium_name}\\nActivo: {asset_name}\\nFecha de revision: {inspection_date}\\nTecnico/revisor: {technician_name}\\nTipo de revision: {inspection_type}\\nEstado general: {general_status}\\nPuertas: {doors_status}\\nCabina: {cabin_status}\\nBotonera y senaletica: {controls_status}\\nSala de maquinas: {machine_room_status}\\nFoso: {pit_status}\\nRuidos o vibraciones: {noise_or_vibration}\\nHallazgos: {findings}\\nTrabajos realizados: {actions_performed}\\nRecomendaciones: {recommendations}\\nEvidencias: {evidence_summary}\\nHistorial del activo: {asset_history}\\n\\nDevuelve secciones: resumen ejecutivo, alcance de la revision, estado por componente, trabajos realizados, hallazgos, recomendaciones, urgencia sugerida y pendientes de validacion.',
            '["condominium_name", "asset_name", "inspection_type", "general_status"]'::jsonb,
            '["inspection_date", "technician_name", "doors_status", "cabin_status", "controls_status", "machine_room_status", "pit_status", "noise_or_vibration", "findings", "actions_performed", "recommendations", "evidence_summary", "asset_history"]'::jsonb,
            'deepseek-v4-flash',
            0.2,
            1400,
            'active',
            TRUE,
            '{"seeded": true, "source": "migration"}'::jsonb
        ),
        (
            '019f76e6-2130-7000-9000-000000000002',
            'operational_report_draft',
            'Borrador de informe operativo',
            'Informe general de servicio o mantencion operacional.',
            'operational_report_draft',
            'operations',
            NULL,
            'Eres Komite, un asistente operativo para administracion de condominios en Chile. Redactas informes verificables, sobrios y utiles para administradores, comites y proveedores. No inventes datos. Si falta informacion, dejala marcada como pendiente.',
            'Genera un borrador profesional para un informe de servicio.\\n\\nCondominio: {condominium_name}\\nTrabajo: {event_title}\\nActivo/equipo: {asset_name}\\nDescripcion programada: {event_description}\\nComentarios de ejecucion: {execution_comments}\\nEvidencias: {evidence_summary}\\nHistorial del activo: {asset_history}\\n\\nDevuelve secciones: resumen ejecutivo, trabajos realizados, incidencias detectadas, recomendaciones y pendientes de validacion.',
            '["event_title", "condominium_name"]'::jsonb,
            '["event_description", "execution_comments", "asset_name", "evidence_summary", "asset_history"]'::jsonb,
            'deepseek-v4-flash',
            0.2,
            1400,
            'active',
            TRUE,
            '{"seeded": true, "source": "migration"}'::jsonb
        )
        ON CONFLICT ("id") DO NOTHING;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "ai_prompt_templates";
    """
