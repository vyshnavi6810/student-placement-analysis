-- ONE-TIME migration: existing database to multi-university
-- Run only after confirming an Aiven backup is available.
-- Existing records will be assigned to MBU.

CREATE TABLE IF NOT EXISTS universities (
    university_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    slug VARCHAR(80) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO universities (name, slug)
VALUES
('Mohan Babu University', 'mbu'),
('ABC University', 'abc-university'),
('XYZ College', 'xyz-college');

SET @mbu_id = (
    SELECT university_id
    FROM universities
    WHERE slug = 'mbu'
);

-- Add university columns
ALTER TABLE student_accounts ADD COLUMN university_id INT NULL;
ALTER TABLE students ADD COLUMN university_id INT NULL;
ALTER TABLE skills ADD COLUMN university_id INT NULL;
ALTER TABLE student_skills ADD COLUMN university_id INT NULL;
ALTER TABLE placements ADD COLUMN university_id INT NULL;
ALTER TABLE placement_submissions ADD COLUMN university_id INT NULL;

-- Add only the columns that do not already exist
ALTER TABLE students ADD COLUMN user_id INT NULL;
ALTER TABLE placement_submissions ADD COLUMN admin_remarks TEXT NULL;

-- Assign existing records to MBU
UPDATE student_accounts SET university_id = @mbu_id;
UPDATE students SET university_id = @mbu_id;
UPDATE skills SET university_id = @mbu_id;
UPDATE placements SET university_id = @mbu_id;
UPDATE placement_submissions SET university_id = @mbu_id;

UPDATE student_skills ss
JOIN students s ON s.student_id = ss.student_id
SET ss.university_id = s.university_id;

-- Do not guess student account mappings.
-- students.user_id remains NULL until a verified mapping is available.

-- Make university assignment mandatory
ALTER TABLE student_accounts
    MODIFY university_id INT NOT NULL;

ALTER TABLE students
    MODIFY university_id INT NOT NULL;

ALTER TABLE skills
    MODIFY university_id INT NOT NULL;

ALTER TABLE student_skills
    MODIFY university_id INT NOT NULL;

ALTER TABLE placements
    MODIFY university_id INT NOT NULL;

ALTER TABLE placement_submissions
    MODIFY university_id INT NOT NULL;

-- Change skill uniqueness from global to university-specific
ALTER TABLE skills
    DROP INDEX skill_name,
    ADD UNIQUE KEY uq_skill_university_name
        (university_id, skill_name);

-- Add university foreign keys
ALTER TABLE student_accounts
    ADD CONSTRAINT fk_account_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);

ALTER TABLE students
    ADD CONSTRAINT fk_student_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);

ALTER TABLE skills
    ADD CONSTRAINT fk_skill_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);

ALTER TABLE placements
    ADD CONSTRAINT fk_placement_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);

ALTER TABLE placement_submissions
    ADD CONSTRAINT fk_submission_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);

ALTER TABLE student_skills
    ADD CONSTRAINT fk_student_skills_university
    FOREIGN KEY (university_id)
    REFERENCES universities (university_id);