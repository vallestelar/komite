from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "condominium_inspection_templates"
            ADD COLUMN IF NOT EXISTS "template_type" VARCHAR(80) NOT NULL DEFAULT 'maintenance';

        UPDATE "condominium_inspection_templates" cit
        SET "template_type" = it."template_type"
        FROM "inspection_templates" it
        WHERE cit."base_template_id" = it."id"
          AND it."template_type" IS NOT NULL;

        CREATE INDEX IF NOT EXISTS "idx_cond_ins_templates_template_type"
            ON "condominium_inspection_templates" ("template_type");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_cond_ins_templates_template_type";
        ALTER TABLE "condominium_inspection_templates" DROP COLUMN IF EXISTS "template_type";
    """
