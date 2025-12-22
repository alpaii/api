-- Migration: Add unique constraints and make short_name NOT NULL
-- Date: 2025-12-22

-- Step 1: Update any NULL short_name values to prevent constraint violation
-- (This is just a safety measure - you should verify there are no NULL values first)
UPDATE composers SET short_name = name WHERE short_name IS NULL OR short_name = '';

-- Step 2: Add unique constraint to name column
ALTER TABLE composers ADD UNIQUE INDEX idx_composers_name_unique (name);

-- Step 3: Modify short_name to be NOT NULL and add unique constraint
ALTER TABLE composers
  MODIFY COLUMN short_name VARCHAR(50) NOT NULL COMMENT 'Short name or nickname',
  ADD UNIQUE INDEX idx_composers_short_name_unique (short_name);

-- Verify the changes
SHOW CREATE TABLE composers;
