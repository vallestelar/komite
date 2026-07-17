from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "accounting_periods" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(120) NOT NULL,
            "description" TEXT,
            "start_date" DATE NOT NULL,
            "end_date" DATE NOT NULL,
            "status" VARCHAR(30) NOT NULL DEFAULT 'draft',
            "is_active" BOOL NOT NULL DEFAULT False,
            "reserve_fund_rate" DECIMAL(7,4) NOT NULL DEFAULT 0,
            "closed_at" TIMESTAMPTZ,
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_accounting_periods_company" ON "accounting_periods" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_periods_cond_status" ON "accounting_periods" ("condominium_id", "status");
        CREATE INDEX IF NOT EXISTS "idx_accounting_periods_cond_start" ON "accounting_periods" ("condominium_id", "start_date");
        CREATE INDEX IF NOT EXISTS "idx_accounting_periods_active" ON "accounting_periods" ("is_active");

        CREATE TABLE IF NOT EXISTS "accounting_suppliers" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(180) NOT NULL,
            "rut" VARCHAR(30),
            "email" VARCHAR(255),
            "phone" VARCHAR(40),
            "category" VARCHAR(80),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "notes" TEXT,
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_accounting_suppliers_company" ON "accounting_suppliers" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_suppliers_cond" ON "accounting_suppliers" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_suppliers_name" ON "accounting_suppliers" ("name");
        CREATE INDEX IF NOT EXISTS "idx_accounting_suppliers_status" ON "accounting_suppliers" ("status");

        CREATE TABLE IF NOT EXISTS "accounting_income_types" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(120) NOT NULL,
            "code" VARCHAR(60),
            "status" VARCHAR(30) NOT NULL DEFAULT 'active',
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID REFERENCES "condominiums" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_accounting_income_types_company" ON "accounting_income_types" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_income_types_cond" ON "accounting_income_types" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_income_types_name" ON "accounting_income_types" ("name");
        CREATE INDEX IF NOT EXISTS "idx_accounting_income_types_status" ON "accounting_income_types" ("status");

        CREATE TABLE IF NOT EXISTS "accounting_incomes" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "income_date" DATE NOT NULL,
            "description" TEXT NOT NULL,
            "amount" DECIMAL(14,2) NOT NULL,
            "payment_method" VARCHAR(60),
            "status" VARCHAR(30) NOT NULL DEFAULT 'confirmed',
            "reference" VARCHAR(120),
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "period_id" UUID NOT NULL REFERENCES "accounting_periods" ("id") ON DELETE CASCADE,
            "unit_id" UUID REFERENCES "units" ("id") ON DELETE SET NULL,
            "income_type_id" UUID REFERENCES "accounting_income_types" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_company" ON "accounting_incomes" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_cond_period" ON "accounting_incomes" ("condominium_id", "period_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_unit" ON "accounting_incomes" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_type" ON "accounting_incomes" ("income_type_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_date" ON "accounting_incomes" ("income_date");
        CREATE INDEX IF NOT EXISTS "idx_accounting_incomes_status" ON "accounting_incomes" ("status");

        CREATE TABLE IF NOT EXISTS "accounting_expenses" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "expense_date" DATE NOT NULL,
            "description" TEXT NOT NULL,
            "amount" DECIMAL(14,2) NOT NULL,
            "category" VARCHAR(80),
            "document_number" VARCHAR(120),
            "is_common_expense" BOOL NOT NULL DEFAULT True,
            "status" VARCHAR(30) NOT NULL DEFAULT 'approved',
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "period_id" UUID NOT NULL REFERENCES "accounting_periods" ("id") ON DELETE CASCADE,
            "supplier_id" UUID REFERENCES "accounting_suppliers" ("id") ON DELETE SET NULL,
            "attachment_id" UUID REFERENCES "attachments" ("id") ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_company" ON "accounting_expenses" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_cond_period" ON "accounting_expenses" ("condominium_id", "period_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_supplier" ON "accounting_expenses" ("supplier_id");
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_date" ON "accounting_expenses" ("expense_date");
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_category" ON "accounting_expenses" ("category");
        CREATE INDEX IF NOT EXISTS "idx_accounting_expenses_status" ON "accounting_expenses" ("status");

        CREATE TABLE IF NOT EXISTS "common_expense_runs" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "status" VARCHAR(30) NOT NULL DEFAULT 'draft',
            "total_expenses" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "reserve_fund_rate" DECIMAL(7,4) NOT NULL DEFAULT 0,
            "total_reserve_fund" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "total_charged" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "calculated_at" TIMESTAMPTZ,
            "published_at" TIMESTAMPTZ,
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "period_id" UUID NOT NULL REFERENCES "accounting_periods" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_common_expense_runs_company" ON "common_expense_runs" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_runs_cond_period" ON "common_expense_runs" ("condominium_id", "period_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_runs_status" ON "common_expense_runs" ("status");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_runs_calculated" ON "common_expense_runs" ("calculated_at");

        CREATE TABLE IF NOT EXISTS "common_expense_charges" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "proration" DECIMAL(12,6) NOT NULL DEFAULT 0,
            "expense_amount" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "reserve_fund_amount" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "total_amount" DECIMAL(14,2) NOT NULL DEFAULT 0,
            "status" VARCHAR(30) NOT NULL DEFAULT 'draft',
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "run_id" UUID NOT NULL REFERENCES "common_expense_runs" ("id") ON DELETE CASCADE,
            "period_id" UUID NOT NULL REFERENCES "accounting_periods" ("id") ON DELETE CASCADE,
            "unit_id" UUID NOT NULL REFERENCES "units" ("id") ON DELETE CASCADE,
            CONSTRAINT "uid_common_exp_charge_run_unit" UNIQUE ("run_id", "unit_id")
        );
        CREATE INDEX IF NOT EXISTS "idx_common_expense_charges_company" ON "common_expense_charges" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_charges_cond_period" ON "common_expense_charges" ("condominium_id", "period_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_charges_run" ON "common_expense_charges" ("run_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_charges_unit" ON "common_expense_charges" ("unit_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_charges_status" ON "common_expense_charges" ("status");

        CREATE TABLE IF NOT EXISTS "common_expense_charge_items" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "created_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by" VARCHAR(100) NOT NULL DEFAULT 'system',
            "id" UUID NOT NULL PRIMARY KEY,
            "description" TEXT NOT NULL,
            "expense_amount" DECIMAL(14,2) NOT NULL,
            "prorated_amount" DECIMAL(14,2) NOT NULL,
            "metadata" JSONB NOT NULL,
            "company_id" UUID REFERENCES "companies" ("id") ON DELETE CASCADE,
            "condominium_id" UUID NOT NULL REFERENCES "condominiums" ("id") ON DELETE CASCADE,
            "charge_id" UUID NOT NULL REFERENCES "common_expense_charges" ("id") ON DELETE CASCADE,
            "expense_id" UUID NOT NULL REFERENCES "accounting_expenses" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_common_expense_items_company" ON "common_expense_charge_items" ("company_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_items_cond" ON "common_expense_charge_items" ("condominium_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_items_charge" ON "common_expense_charge_items" ("charge_id");
        CREATE INDEX IF NOT EXISTS "idx_common_expense_items_expense" ON "common_expense_charge_items" ("expense_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "common_expense_charge_items";
        DROP TABLE IF EXISTS "common_expense_charges";
        DROP TABLE IF EXISTS "common_expense_runs";
        DROP TABLE IF EXISTS "accounting_expenses";
        DROP TABLE IF EXISTS "accounting_incomes";
        DROP TABLE IF EXISTS "accounting_income_types";
        DROP TABLE IF EXISTS "accounting_suppliers";
        DROP TABLE IF EXISTS "accounting_periods";
    """
