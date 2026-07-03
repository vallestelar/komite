from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "company_profile" VARCHAR(60);

INSERT INTO "roles" ("id", "created_at", "created_by", "updated_at", "updated_by", "code", "name", "description", "permissions", "is_system")
VALUES
    ('01928000-0000-7000-8000-000000000001', CURRENT_TIMESTAMP, 'migration', CURRENT_TIMESTAMP, 'migration', 'vecino', 'Vecino', 'Residente o propietario de la comunidad', '{"scope":"community","community":"read"}'::jsonb, TRUE),
    ('01928000-0000-7000-8000-000000000002', CURRENT_TIMESTAMP, 'migration', CURRENT_TIMESTAMP, 'migration', 'comite', 'Comite', 'Miembro del comite de administracion', '{"scope":"community","committee":"write"}'::jsonb, TRUE),
    ('01928000-0000-7000-8000-000000000003', CURRENT_TIMESTAMP, 'migration', CURRENT_TIMESTAMP, 'migration', 'supervisor', 'Supervisor', 'Usuario operativo de la empresa administradora', '{"scope":"operations","operations":"write"}'::jsonb, TRUE),
    ('01928000-0000-7000-8000-000000000004', CURRENT_TIMESTAMP, 'migration', CURRENT_TIMESTAMP, 'migration', 'conserje', 'Conserje', 'Usuario operativo de conserjeria o terreno', '{"scope":"operations","incidents":"create"}'::jsonb, TRUE)
ON CONFLICT ("code") DO UPDATE SET
    "name" = EXCLUDED."name",
    "description" = EXCLUDED."description",
    "permissions" = EXCLUDED."permissions",
    "is_system" = TRUE,
    "updated_at" = CURRENT_TIMESTAMP,
    "updated_by" = 'migration';

UPDATE "users"
SET "company_profile" = CASE
    WHEN "company_profile" IN ('project_manager', 'ejecutivo') THEN "company_profile"
    WHEN "company_profile" IN ('supervisor', 'conserje') THEN 'ejecutivo'
    WHEN "global_role" IN ('superadmin', 'admin', 'administrador_empresa') THEN 'project_manager'
    WHEN "global_role" IN ('administrador_condominio', 'supervisor', 'conserje') THEN 'ejecutivo'
    ELSE NULL
END;

DELETE FROM "user_condominiums" old_membership
USING "roles" old_role, "roles" supervisor, "user_condominiums" existing_supervisor
WHERE old_membership."role_id" = old_role."id"
  AND supervisor."code" = 'supervisor'
  AND existing_supervisor."role_id" = supervisor."id"
  AND existing_supervisor."user_id" = old_membership."user_id"
  AND existing_supervisor."condominium_id" IS NOT DISTINCT FROM old_membership."condominium_id"
  AND existing_supervisor."unit_id" IS NOT DISTINCT FROM old_membership."unit_id"
  AND old_role."code" NOT IN ('vecino', 'comite', 'supervisor', 'conserje');

DELETE FROM "user_condominiums"
WHERE "id" IN (
    SELECT "id"
    FROM (
        SELECT membership."id",
               ROW_NUMBER() OVER (
                   PARTITION BY membership."user_id", membership."condominium_id", membership."unit_id"
                   ORDER BY membership."created_at", membership."id"
               ) AS duplicate_number
        FROM "user_condominiums" membership
        INNER JOIN "roles" role ON role."id" = membership."role_id"
        WHERE role."code" NOT IN ('vecino', 'comite', 'supervisor', 'conserje')
    ) duplicates
    WHERE duplicates.duplicate_number > 1
);

UPDATE "user_condominiums" target
SET "role_id" = supervisor."id"
FROM "roles" old_role, "roles" supervisor
WHERE target."role_id" = old_role."id"
  AND supervisor."code" = 'supervisor'
  AND old_role."code" NOT IN ('vecino', 'comite', 'supervisor', 'conserje');

DELETE FROM "roles"
WHERE "code" NOT IN ('vecino', 'comite', 'supervisor', 'conserje');

DROP INDEX IF EXISTS "idx_users_global_role";
ALTER TABLE "users" DROP COLUMN IF EXISTS "global_role";
CREATE INDEX IF NOT EXISTS "idx_users_company_profile" ON "users" ("company_profile");

ALTER TABLE "user_condominiums" DROP CONSTRAINT IF EXISTS "uid_user_condom_user_id_324e86";
ALTER TABLE "user_condominiums" ALTER COLUMN "condominium_id" DROP NOT NULL;
ALTER TABLE "user_condominiums"
    ADD CONSTRAINT "chk_user_condom_all_without_unit"
    CHECK ("condominium_id" IS NOT NULL OR "unit_id" IS NULL);

CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_condom_all_company_role"
    ON "user_condominiums" ("user_id", "company_id", "role_id")
    WHERE "condominium_id" IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS "uid_user_condom_specific_role_unit"
    ON "user_condominiums" ("user_id", "condominium_id", "role_id", COALESCE("unit_id", '00000000-0000-0000-0000-000000000000'::uuid))
    WHERE "condominium_id" IS NOT NULL;
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
DROP INDEX IF EXISTS "uid_user_condom_specific_role_unit";
DROP INDEX IF EXISTS "uid_user_condom_all_company_role";
ALTER TABLE "user_condominiums" DROP CONSTRAINT IF EXISTS "chk_user_condom_all_without_unit";
DROP INDEX IF EXISTS "idx_users_company_profile";
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "global_role" VARCHAR(60) DEFAULT 'user';
UPDATE "users" SET "global_role" = 'user' WHERE "global_role" IS NULL;
ALTER TABLE "users" ALTER COLUMN "global_role" SET NOT NULL;
CREATE INDEX IF NOT EXISTS "idx_users_global_role" ON "users" ("global_role");
ALTER TABLE "users" DROP COLUMN IF EXISTS "company_profile";
"""
