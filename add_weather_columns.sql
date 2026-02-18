-- Add weather columns to practice_notes table
ALTER TABLE practice_notes 
ADD COLUMN IF NOT EXISTS temperature INTEGER,
ADD COLUMN IF NOT EXISTS wind_speed INTEGER,
ADD COLUMN IF NOT EXISTS wind_direction VARCHAR(10);
