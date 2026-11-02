-- Database creation---
CREATE DATABASE student_placement_analysis;
USE student_placement_analysis;

-- 1. Student details and placement eligibility
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(30) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    graduation_year YEAR NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. List of technical  skills and other skills
CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE
);

-- 3. relationship between students and skills
CREATE TABLE student_skills (
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,
    FOREIGN KEY (skill_id)
        REFERENCES skills(skill_id)
        ON DELETE CASCADE
);

-- 4. Company applications and placement status
CREATE TABLE placements (
    placement_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    company VARCHAR(150) NOT NULL,
    role VARCHAR(150) NOT NULL,
    package_lpa DECIMAL(8,2),
    placement_date DATE,
    status ENUM(
        'APPLIED',
        'SELECTED',
        'PLACED',
        'REJECTED',
        'WITHDRAWN'
    ) NOT NULL DEFAULT 'APPLIED',
    FOREIGN KEY (student_id)
        REFERENCES students(student_id),
    CHECK (package_lpa IS NULL OR package_lpa >= 0),
    INDEX idx_placement_status (status),
    INDEX idx_placement_company (company)
);






CREATE TABLE IF NOT EXISTS student_accounts (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS placement_submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100) NOT NULL,
    skills TEXT,
    placement_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    company VARCHAR(150),
    job_role VARCHAR(150),
    package_lpa DECIMAL(8,2),
    verification_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    verified_by VARCHAR(50),
    FOREIGN KEY (user_id)
        REFERENCES student_accounts(user_id)
        ON DELETE CASCADE
);


SHOW TABLES;


INSERT IGNORE INTO students (roll_no, department, graduation_year, is_eligible) VALUES
-- CSE: 25102A04 series
('25102A040011', 'CSE', 2029, TRUE),
('25102A040012', 'CSE', 2029, TRUE),
('25102A040013', 'CSE', 2029, FALSE),
('25102A040014', 'CSE', 2029, TRUE),
('25102A040015', 'CSE', 2029, FALSE),
('25102A040016', 'CSE', 2029, TRUE),
('25102A040017', 'CSE', 2029, TRUE),
('25102A040018', 'CSE', 2029, FALSE),
('25102A040019', 'CSE', 2029, TRUE),
('25102A040020', 'CSE', 2029, TRUE),
-- AI&ML: 25102A01 series
('25102A010011', 'AI&ML', 2029, TRUE),
('25102A010012', 'AI&ML', 2029, FALSE),
('25102A010013', 'AI&ML', 2029, TRUE),
('25102A010014', 'AI&ML', 2029, TRUE),
('25102A010015', 'AI&ML', 2029, FALSE),
('25102A010016', 'AI&ML', 2029, TRUE),
('25102A010017', 'AI&ML', 2029, TRUE),
('25102A010018', 'AI&ML', 2029, FALSE),
('25102A010019', 'AI&ML', 2029, TRUE),
('25102A010020', 'AI&ML', 2029, TRUE),
-- AI&DS: 25102A02 series used here as sample data; verify official code with college
('25102A020011', 'AI&DS', 2029, TRUE),
('25102A020012', 'AI&DS', 2029, TRUE),
('25102A020013', 'AI&DS', 2029, FALSE),
('25102A020014', 'AI&DS', 2029, TRUE),
('25102A020015', 'AI&DS', 2029, FALSE),
('25102A020016', 'AI&DS', 2029, TRUE),
('25102A020017', 'AI&DS', 2029, TRUE),
('25102A020018', 'AI&DS', 2029, FALSE),
('25102A020019', 'AI&DS', 2029, TRUE),
('25102A020020', 'AI&DS', 2029, TRUE);

-- 4. Skill catalogue
INSERT IGNORE INTO skills (skill_name) VALUES
('Python'), ('Java'), ('SQL'), ('Web Development'), ('Data Structures'),
('Machine Learning'), ('Statistics'), ('Data Visualization'), ('Deep Learning'), ('Communication');

-- 5. Skill assignments use roll_no lookups, not assumed auto-increment IDs
INSERT IGNORE INTO student_skills (student_id, skill_id)
SELECT s.student_id, sk.skill_id
FROM students s
JOIN skills sk ON (
    (s.roll_no IN ('25102A040011', '25102A010011', '25102A020011')
        AND sk.skill_name IN ('Python', 'SQL'))
 OR (s.roll_no IN ('25102A040012', '25102A010013', '25102A020012')
        AND sk.skill_name IN ('Java', 'Data Structures'))
 OR (s.roll_no IN ('25102A010014', '25102A020014')
        AND sk.skill_name IN ('Machine Learning', 'Python', 'Statistics'))
 OR (s.roll_no IN ('25102A040016', '25102A010016', '25102A020016')
        AND sk.skill_name IN ('SQL', 'Data Visualization'))
);

-- 6. Illustrative placement/application data
INSERT INTO placements (student_id, company, role, package_lpa, placement_date, status) SELECT student_id, 'TCS', 'Data Analyst', 6.00, '2026-08-10', 'PLACED' FROM students WHERE roll_no = '25102A040011' AND is_eligible = TRUE;
INSERT INTO placements (student_id, company, role, package_lpa, placement_date, status) SELECT student_id, 'Infosys', 'Software Engineer', 8.00, '2026-08-15', 'PLACED' FROM students WHERE roll_no = '25102A040012' AND is_eligible = TRUE;
INSERT INTO placements (student_id, company, role, package_lpa, placement_date, status) SELECT student_id, 'Wipro', 'Software Engineer', 5.00, '2026-08-20', 'PLACED' FROM students WHERE roll_no = '25102A010011' AND is_eligible = TRUE;
INSERT INTO placements (student_id, company, role, package_lpa, placement_date, status) SELECT student_id, 'Accenture', 'Associate Software Engineer', NULL, NULL, 'APPLIED' FROM students WHERE roll_no = '25102A020011';

-- 7. Analysis queries
SELECT COUNT(*) AS total_students FROM students;
SELECT department, COUNT(*) AS total_students, SUM(is_eligible=TRUE) AS eligible_students, SUM(is_eligible=FALSE) AS ineligible_students FROM students GROUP BY department ORDER BY department;
SELECT roll_no, department, graduation_year, IF(is_eligible,'Eligible','Not Eligible') AS eligibility FROM students ORDER BY department, roll_no;
SELECT s.roll_no, s.department, sk.skill_name FROM students s JOIN student_skills ss ON ss.student_id=s.student_id JOIN skills sk ON sk.skill_id=ss.skill_id ORDER BY s.roll_no, sk.skill_name;
SELECT company, role, status, COUNT(*) AS student_count, ROUND(AVG(package_lpa),2) AS average_package_lpa FROM placements GROUP BY company, role, status ORDER BY company, role;
SELECT s.department, COUNT(p.placement_id) AS placed_students, ROUND(AVG(CASE WHEN p.status='PLACED' THEN p.package_lpa END),2) AS avg_package_lpa FROM students s LEFT JOIN placements p ON p.student_id=s.student_id AND p.status='PLACED' GROUP BY s.department ORDER BY s.department;
SELECT s.roll_no, s.department, p.company, p.role, p.package_lpa, p.status FROM students s JOIN placements p ON p.student_id=s.student_id ORDER BY p.status, s.roll_no;
-- End of project script.



USE student_placement_analysis;

-- Run this once on an existing database. If a column already exists,
-- skip that individual ALTER TABLE statement.
ALTER TABLE placement_submissions
    ADD COLUMN roll_no VARCHAR(30) NULL AFTER user_id;

ALTER TABLE placement_submissions
    ADD COLUMN graduation_year YEAR NULL AFTER department;

ALTER TABLE placement_submissions
    ADD COLUMN is_eligible BOOLEAN NOT NULL DEFAULT TRUE AFTER graduation_year;

-- Make the fields mandatory after the existing pending rows have been reviewed
-- or backfilled. New submissions through the Flask form always provide them.




