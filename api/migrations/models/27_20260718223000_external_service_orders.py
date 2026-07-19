from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "external_service_orders" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "token_hash" VARCHAR(128) NOT NULL UNIQUE,
            "title" VARCHAR(180) NOT NULL,
            "instructions" TEXT,
            "provider_name" VARCHAR(160) NOT NULL,
            "provider_email" VARCHAR(255),
            "provider_phone" VARCHAR(40),
            "prompt_key" VARCHAR(120) NOT NULL DEFAULT 'vendor_service_report',
            "status" VARCHAR(40) NOT NULL DEFAULT 'pending',
            "expires_at" TIMESTAMPTZ,
            "submitted_at" TIMESTAMPTZ,
            "submission_payload" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "ai_generated_text" TEXT,
            "public_url" VARCHAR(500),
            "metadata" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "event_id" UUID NOT NULL REFERENCES "planned_operational_events" ("id") ON DELETE CASCADE,
            "asset_id" UUID REFERENCES "condominium_assets" ("id") ON DELETE SET NULL,
            "execution_id" UUID REFERENCES "operational_event_executions" ("id") ON DELETE SET NULL,
            "ai_prompt_template_id" UUID REFERENCES "ai_prompt_templates" ("id") ON DELETE SET NULL,
            "ai_request_id" UUID REFERENCES "ai_requests" ("id") ON DELETE SET NULL,
            "report_id" UUID REFERENCES "reports" ("id") ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_company_id" ON "external_service_orders" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_condominium_id" ON "external_service_orders" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_event_id" ON "external_service_orders" ("event_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_asset_id" ON "external_service_orders" ("asset_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_execution_id" ON "external_service_orders" ("execution_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_ai_prompt_template_id" ON "external_service_orders" ("ai_prompt_template_id");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_status" ON "external_service_orders" ("status");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_expires_at" ON "external_service_orders" ("expires_at");
        CREATE INDEX IF NOT EXISTS "idx_external_service_orders_submitted_at" ON "external_service_orders" ("submitted_at");

        INSERT INTO "ai_prompt_templates" (
            "id", "key", "name", "description", "purpose", "module", "asset_type",
            "system_template", "user_template", "required_variables", "optional_variables",
            "default_model", "default_temperature", "default_max_tokens", "status", "is_active", "metadata"
        )
        VALUES (
            '019f76e6-2230-7000-9000-000000000001',
            'vendor_service_report',
            'Informe proveedor externo',
            'Borrador de informe generado desde un formulario publico completado por proveedor externo.',
            'vendor_service_report',
            'operations',
            NULL,
            'Actuas como asistente operativo de Komite para administracion de condominios en Chile. Redactas informes de servicio a partir de datos enviados por proveedores externos. No inventes datos. Si falta informacion relevante, mencionas el dato faltante dentro de la seccion correspondiente. El tono debe ser profesional, claro y verificable para administrador, comite y proveedor.',
            'Genera un informe de servicio editable con los datos del proveedor.\\n\\nCondominio: {condominium_name}\\nTrabajo solicitado: {event_title}\\nActivo/equipo: {asset_name}\\nProveedor: {provider_name}\\nResponsable que informa: {submitted_by_name}\\nFecha de ejecucion: {execution_date}\\nResultado declarado: {result}\\nInstrucciones originales: {instructions}\\nTrabajo realizado: {work_performed}\\nHallazgos: {findings}\\nMateriales o repuestos: {materials_used}\\nRecomendaciones: {recommendations}\\nProxima visita requerida: {next_visit_required}\\nComentarios adicionales: {additional_comments}\\n\\nDevuelve secciones: resumen ejecutivo, trabajo realizado, hallazgos, recomendaciones y observaciones para el administrador. No agregues costos ni garantias si no fueron informados. Usa fechas en formato DD/MM/AAAA. No incluyas separadores Markdown como --- o --. No incluyas firma, "Elaborado por", "Eres Komite" ni "Estado del informe". Si no recibes numero de orden, omite esa linea; no escribas [Pendiente].',
            '["condominium_name", "event_title", "provider_name", "work_performed"]'::jsonb,
            '["asset_name", "submitted_by_name", "execution_date", "result", "instructions", "findings", "materials_used", "recommendations", "next_visit_required", "additional_comments"]'::jsonb,
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
        DROP TABLE IF EXISTS "external_service_orders";
        DELETE FROM "ai_prompt_templates" WHERE "id" = '019f76e6-2230-7000-9000-000000000001';
    """
