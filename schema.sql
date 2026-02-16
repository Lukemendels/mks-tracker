-- 1. TABLES DEFINITION

-- Core Axioms of the Mendelsohn Kernel Standard
CREATE TABLE mindset_axioms (
    id SERIAL PRIMARY KEY,
    short_name VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    corollary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hole-by-hole strategy and relational mapping
CREATE TABLE course_metadata (
    id SERIAL PRIMARY KEY,
    hole_number INTEGER NOT NULL,
    layout VARCHAR(50) NOT NULL, -- e.g., 'Shorts (Round 1)'
    protocol_notes TEXT,
    axiom_id INTEGER REFERENCES mindset_axioms(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hole_number, layout) -- Prevents duplicate strategy entries
);

-- Practice session logs
CREATE TABLE practice_notes (
    id SERIAL PRIMARY KEY,
    hole_number INTEGER NOT NULL,
    layout VARCHAR(50) NOT NULL,
    disc_used VARCHAR(100),
    result_rating INTEGER CHECK (result_rating BETWEEN 1 AND 5),
    strokes INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. SEED DATA (Axioms)
INSERT INTO mindset_axioms (id, short_name, title, corollary) VALUES
(1, 'Axiom I', 'THE LAW OF BORING GOLF', 'The Sexton Principle'),
(2, 'Axiom II', 'EMOTIONAL NEUTRALITY', 'The Conrad Doctrine'),
(3, 'Axiom III', 'DATA OVER MEMORY', 'The McBeth Corollary'),
(4, 'Axiom IV', 'ALL GAS UNTIL NO BRAKES ARE NEEDED', 'The Klein Strategy'),
(5, 'Axiom V', 'COMPETING AT THE CEILING', 'Maximizing potential through execution');

-- 3. ENABLE ROW LEVEL SECURITY (RLS) - Recommended for Supabase
ALTER TABLE mindset_axioms ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_notes ENABLE ROW LEVEL SECURITY;

-- Create policies (Example: Allow authenticated users to read)
CREATE POLICY "Allow auth read" ON mindset_axioms FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow auth read" ON course_metadata FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow auth all" ON practice_notes FOR ALL TO authenticated USING (true);
