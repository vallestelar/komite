from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
CREATE TABLE IF NOT EXISTS "refresh_tokens" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
    "id" UUID NOT NULL PRIMARY KEY,
    "token_hash" VARCHAR(64) NOT NULL UNIQUE,
    "family_id" UUID NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "revoked_at" TIMESTAMPTZ,
    "created_by_ip" VARCHAR(80),
    "user_agent" VARCHAR(255),
    "replaced_by_id" UUID REFERENCES "refresh_tokens" ("id") ON DELETE SET NULL,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_refresh_to_user_id_5b1688" ON "refresh_tokens" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_refresh_to_token_h_535a83" ON "refresh_tokens" ("token_hash");
CREATE INDEX IF NOT EXISTS "idx_refresh_to_family__73ad92" ON "refresh_tokens" ("family_id");
CREATE INDEX IF NOT EXISTS "idx_refresh_to_expires_62c329" ON "refresh_tokens" ("expires_at");
CREATE INDEX IF NOT EXISTS "idx_refresh_to_revoked_79f62c" ON "refresh_tokens" ("revoked_at");
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
DROP TABLE IF EXISTS "refresh_tokens";
"""
