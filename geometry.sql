-- Create the hole_geometry table
CREATE TABLE IF NOT EXISTS hole_geometry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hole_number INTEGER NOT NULL,
    layout VARCHAR(50) NOT NULL,
    tee_lat DOUBLE PRECISION,
    tee_lon DOUBLE PRECISION,
    basket_lat DOUBLE PRECISION,
    basket_lon DOUBLE PRECISION,
    distance_feet DOUBLE PRECISION,
    elevation_change_feet DOUBLE PRECISION,
    mapped_by UUID REFERENCES auth.users(id),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hole_number, layout)
);

-- Enable Row Level Security
ALTER TABLE hole_geometry ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous read access
CREATE POLICY "Enable read access for all users" 
ON hole_geometry FOR SELECT 
TO anon, authenticated
USING (true);

-- Policy: Allow authenticated insert
CREATE POLICY "Enable insert for authenticated users only" 
ON hole_geometry FOR INSERT 
TO authenticated 
WITH CHECK (true);

-- Policy: Allow authenticated update if they are the mapper (or generic auth for now as requirements were just 'authenticated')
-- Updating requirement to strictly follow "Allow 'authenticated' users to INSERT/UPDATE"
CREATE POLICY "Enable update for authenticated users" 
ON hole_geometry FOR UPDATE 
TO authenticated 
USING (true)
WITH CHECK (true);
