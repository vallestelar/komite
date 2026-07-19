from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "ai_prompt_templates"
        SET
            "system_template" = 'Actuas como asistente operativo de Komite para administracion de condominios en Chile. Redactas informes de servicio a partir de datos enviados por proveedores externos. No inventes datos. Si falta informacion relevante, mencionas el dato faltante dentro de la seccion correspondiente. El tono debe ser profesional, claro y verificable para administrador, comite y proveedor.',
            "user_template" = 'Genera un informe de servicio editable con los datos del proveedor.\n\nCondominio: {condominium_name}\nTrabajo solicitado: {event_title}\nActivo/equipo: {asset_name}\nProveedor: {provider_name}\nResponsable que informa: {submitted_by_name}\nFecha de ejecucion: {execution_date}\nResultado declarado: {result}\nInstrucciones originales: {instructions}\nTrabajo realizado: {work_performed}\nHallazgos: {findings}\nMateriales o repuestos: {materials_used}\nRecomendaciones: {recommendations}\nProxima visita requerida: {next_visit_required}\nComentarios adicionales: {additional_comments}\n\nDevuelve secciones: resumen ejecutivo, trabajo realizado, hallazgos, recomendaciones y observaciones para el administrador. No agregues costos ni garantias si no fueron informados. Usa fechas en formato DD/MM/AAAA. No incluyas separadores Markdown como --- o --. No incluyas firma, "Elaborado por", "Eres Komite" ni "Estado del informe". Si no recibes numero de orden, omite esa linea; no escribas [Pendiente].',
            "updated_by" = 'migration_29_harden_vendor_service_prompt'
        WHERE "id" = '019f76e6-2230-7000-9000-000000000001'
          AND "key" = 'vendor_service_report'
          AND "company_id" IS NULL
          AND "condominium_id" IS NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE "ai_prompt_templates"
        SET
            "system_template" = 'Eres Komite, asistente operativo para administracion de condominios en Chile. Redactas informes de servicio a partir de datos enviados por proveedores externos. No inventes datos. Si falta informacion, dejala como pendiente. El tono debe ser profesional, claro y verificable para administrador, comite y proveedor.',
            "user_template" = 'Genera un informe de servicio editable con los datos del proveedor.\n\nCondominio: {condominium_name}\nTrabajo solicitado: {event_title}\nActivo/equipo: {asset_name}\nProveedor: {provider_name}\nResponsable que informa: {submitted_by_name}\nFecha de ejecucion: {execution_date}\nResultado declarado: {result}\nInstrucciones originales: {instructions}\nTrabajo realizado: {work_performed}\nHallazgos: {findings}\nMateriales o repuestos: {materials_used}\nRecomendaciones: {recommendations}\nProxima visita requerida: {next_visit_required}\nComentarios adicionales: {additional_comments}\n\nDevuelve secciones: resumen ejecutivo, trabajo realizado, hallazgos, recomendaciones, pendientes de validacion y observaciones para el administrador. No agregues costos ni garantias si no fueron informados.',
            "updated_by" = 'migration_29_harden_vendor_service_prompt_rollback'
        WHERE "id" = '019f76e6-2230-7000-9000-000000000001'
          AND "key" = 'vendor_service_report'
          AND "company_id" IS NULL
          AND "condominium_id" IS NULL;
    """
