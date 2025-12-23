-- Migration: Rename name -> full_name and short_name -> name
-- Date: 2025-12-23

-- Step 1: Rename name to full_name first
ALTER TABLE composers CHANGE COLUMN name full_name VARCHAR(100) NOT NULL COMMENT 'Full name in English';

-- Step 2: Rename short_name to name
ALTER TABLE composers CHANGE COLUMN short_name name VARCHAR(50) NOT NULL COMMENT 'Short name or nickname';

-- Verify the changes
SHOW CREATE TABLE composers;
