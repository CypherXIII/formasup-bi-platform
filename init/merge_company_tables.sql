-- Migration script: Merge company_info columns into company table
-- Backup: staging_backup_20260113_135525.dump
-- Date: 2026-01-13

BEGIN;

-- Step 1: Add new columns to company table (from company_info)
ALTER TABLE staging.company
    ADD COLUMN IF NOT EXISTS name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS city_id INTEGER,
    ADD COLUMN IF NOT EXISTS idcc_id INTEGER,
    ADD COLUMN IF NOT EXISTS naf_id INTEGER,
    ADD COLUMN IF NOT EXISTS workforce INTEGER,
    ADD COLUMN IF NOT EXISTS category VARCHAR(255),
    ADD COLUMN IF NOT EXISTS type_id INTEGER,
    ADD COLUMN IF NOT EXISTS opco_id INTEGER,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();

-- Step 2: Copy data from company_info to company
-- Convert 0 values to NULL for FK compatibility
UPDATE staging.company c
SET
    name = ci.name,
    city_id = NULLIF(ci.city_id, 0),
    idcc_id = NULLIF(ci.idcc_id, 0),
    naf_id = NULLIF(ci.naf_id, 0),
    workforce = ci.workforce,
    category = ci.category,
    type_id = NULLIF(ci.type_id, 0),
    opco_id = NULLIF(ci.opco_id, 0),
    created_at = ci.created_at
FROM staging.company_info ci
WHERE c.id = ci.id;

-- Step 3: Add foreign key constraints
ALTER TABLE staging.company
    ADD CONSTRAINT company_city_id_fkey
        FOREIGN KEY (city_id) REFERENCES staging.city(id) ON DELETE SET NULL,
    ADD CONSTRAINT company_idcc_id_fkey
        FOREIGN KEY (idcc_id) REFERENCES staging.idcc(id) ON DELETE SET NULL,
    ADD CONSTRAINT company_naf_id_fkey
        FOREIGN KEY (naf_id) REFERENCES staging.naf(id) ON DELETE SET NULL,
    ADD CONSTRAINT company_type_id_fkey
        FOREIGN KEY (type_id) REFERENCES staging.company_type(id) ON DELETE SET NULL,
    ADD CONSTRAINT company_opco_id_fkey
        FOREIGN KEY (opco_id) REFERENCES staging.opco(id) ON DELETE SET NULL;

-- Step 4: Drop company_info table
DROP TABLE IF EXISTS staging.company_info CASCADE;

-- Step 5: Verify migration
SELECT
    COUNT(*) as total_companies,
    COUNT(name) as with_name,
    COUNT(naf_id) as with_naf,
    COUNT(opco_id) as with_opco
FROM staging.company;

COMMIT;
