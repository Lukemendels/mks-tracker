-- Create the discs table
CREATE TABLE discs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plastic VARCHAR(100),
    weight VARCHAR(50),
    notes TEXT,
    speed NUMERIC,
    glide NUMERIC,
    turn NUMERIC,
    fade NUMERIC,
    disc_type VARCHAR(50), -- Putter, Approach, Midrange, Fairway Driver, Distance Driver
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE discs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow auth read" ON discs FOR SELECT TO authenticated USING (true);

-- Insert seed data
INSERT INTO discs (name, plastic, weight, notes, speed, glide, turn, fade, disc_type) VALUES
('Watt', 'Neutron', '174 g', 'Putting putter. Rarely used for driving, but available if needed.', 2, 5, -0.5, 0.5, 'Putter'),
('Zone', 'ESP FLX', '173 g', 'Go-to approach disc. Thrown almost all the time on approach.', 4, 3, 0, 3, 'Approach'),
('Caiman', 'Champion', '173.5 g', NULL, 5.5, 2, 0, 4, 'Midrange'),
('Mako', 'Star', '176 g', NULL, 5, 5, 0, 0, 'Midrange'),
('Fox', 'Halo Star', '180 g', NULL, 5, 6, -2, 1, 'Midrange'),
('Teebird', 'DX', '172 g', 'Thrown in the open field and for the water carry on hole 10.', 7, 5, 0, 2, 'Fairway Driver'),
('Leopard3', 'Star', '173.5 g', NULL, 7, 5, -2, 1, 'Fairway Driver'),
('Firebird', 'Champion', '173.5 g', 'Slightly beat in.', 9, 3, 0, 4, 'Fairway Driver'),
('Thunderbird', 'Champion', '173 g', 'Updated weight.', 9, 5, 0, 2, 'Fairway Driver'),
('TL3', NULL, '173.5 g', 'New disc, haven\'t thrown yet.', 8, 4, -1, 1, 'Fairway Driver'),
('Buzzz', 'ESP FLX', '177 g', 'Borrowed disc, but counting it for the tournament.', 5, 4, -1, 1, 'Midrange'),
('Heat', 'ESP', '169 g', 'Updated weight.', 9, 6, -3, 1, 'Fairway Driver'),
('Trail', 'Neutron', '170 g', NULL, 10, 5, -1, 1, 'Distance Driver'),
('Wraith', 'Star (I-Dye)', '171 g', NULL, 11, 5, -1, 3, 'Distance Driver'),
('Saint', 'Retro', '173 g', NULL, 9, 7, -1, 2, 'Fairway Driver'),
('Destroyer', 'DX', '175 g', NULL, 12, 5, -1, 3, 'Distance Driver');
