-- 0. CLEANUP DATA (Crucial Step!)
-- The error "Key (suggested_disc)=() is not present" means you have empty strings.
-- We must convert them to NULL before linking, because NULL means "no link", 
-- but "" (empty string) tries to look for a disc named "".

UPDATE course_metadata 
SET suggested_disc = NULL 
WHERE suggested_disc = '' OR suggested_disc IS NULL;

-- 1. Ensure disc names are unique (Required for Foreign Key)
-- (If you already ran this part successfully, you can skip it or ignore the 'already exists' error)
ALTER TABLE discs ADD CONSTRAINT discs_name_key UNIQUE (name);

-- 2. Add Foreign Key Constraint
ALTER TABLE course_metadata 
ADD CONSTRAINT fk_suggested_disc
FOREIGN KEY (suggested_disc) 
REFERENCES discs (name)
ON DELETE SET NULL
ON UPDATE CASCADE;
