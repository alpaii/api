-- Migration: Add image_url column to composers table
-- Date: 2025-12-23

-- Add image_url column
ALTER TABLE composers ADD COLUMN image_url VARCHAR(255) NULL COMMENT 'Profile image URL';

-- Verify the changes
SHOW CREATE TABLE composers;
