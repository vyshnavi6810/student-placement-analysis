USE defaultdb;

-- FRESH MULTI-UNIVERSITY DATABASE SETUP
-- WARNING: This permanently deletes the existing project tables and records.

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS placement_submissions;
DROP TABLE IF EXISTS student_skills;
DROP TABLE IF EXISTS placements;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS student_accounts;
DROP TABLE IF EXISTS universities;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Universities
CREATE TABLE universities (
    university_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    slug VARCHAR(80) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO universities (name, slug) VALUES
('Mohan Babu University', 'mbu'),
('ABC University', 'abc-university'),
('XYZ College', 'xyz-college');

-- 2. Student accounts
CREATE TABLE student_accounts (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    university_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_email_university (university_id, email),
    UNIQUE KEY uq_student_username_university (university_id, username),
    UNIQUE KEY uq_account_university_user (university_id, user_id),
    CONSTRAINT fk_account_university
        FOREIGN KEY (university_id)
        REFERENCES universities (university_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Students
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    university_id INT NOT NULL,
    user_id INT NULL,
    roll_no VARCHAR(30) NOT NULL,
    department VARCHAR(100) NOT NULL,
    graduation_year YEAR NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY uq_roll_university (university_id, roll_no),
    UNIQUE KEY uq_student_user_university (university_id, user_id),
    UNIQUE KEY uq_student_university_id (university_id, student_id),
    CONSTRAINT fk_student_university
        FOREIGN KEY (university_id)
        REFERENCES universities (university_id),
    CONSTRAINT fk_student_account
        FOREIGN KEY (user_id)
        REFERENCES student_accounts (user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Skills
CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    university_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_skill_university (university_id, skill_name),
    UNIQUE KEY uq_skill_university_id (university_id, skill_id),
    CONSTRAINT fk_skill_university
        FOREIGN KEY (university_id)
        REFERENCES universities (university_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Student skills
CREATE TABLE student_skills (
    university_id INT NOT NULL,
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (university_id, student_id, skill_id),
    CONSTRAINT fk_ss_student_tenant
        FOREIGN KEY (university_id, student_id)
        REFERENCES students (university_id, student_id) ON DELETE CASCADE,
    CONSTRAINT fk_ss_skill_tenant
        FOREIGN KEY (university_id, skill_id)
        REFERENCES skills (university_id, skill_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Placements
CREATE TABLE placements (
    placement_id INT AUTO_INCREMENT PRIMARY KEY,
    university_id INT NOT NULL,
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
    CONSTRAINT fk_placement_student_tenant
        FOREIGN KEY (university_id, student_id)
        REFERENCES students (university_id, student_id),
    INDEX idx_placement_tenant_status (university_id, status),
    INDEX idx_placement_company (university_id, company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Placement submissions
CREATE TABLE placement_submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    university_id INT NOT NULL,
    user_id INT NOT NULL,
    roll_no VARCHAR(30) NOT NULL,
    department VARCHAR(100) NOT NULL,
    graduation_year YEAR NOT NULL,
    is_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    skills TEXT,
    placement_status VARCHAR(30) NOT NULL DEFAULT 'NOT_PLACED',
    company VARCHAR(150),
    job_role VARCHAR(150),
    package_lpa DECIMAL(8,2),
    verification_status ENUM(
        'Pending',
        'Verified',
        'Rejected'
    ) NOT NULL DEFAULT 'Pending',
    admin_remarks TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    verified_by VARCHAR(50),
    CONSTRAINT fk_submission_university
        FOREIGN KEY (university_id)
        REFERENCES universities (university_id),
    CONSTRAINT fk_submission_account
        FOREIGN KEY (user_id)
        REFERENCES student_accounts (user_id) ON DELETE CASCADE,
    INDEX idx_submission_tenant_status (university_id, verification_status),
    INDEX idx_submission_user (university_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. ABC and XYZ demo students
INSERT INTO students
(university_id, roll_no, department, graduation_year, is_eligible)
SELECT university_id, 'ABC2029CSE001', 'CSE', 2029, 1
FROM universities WHERE slug = 'abc-university';

INSERT INTO students
(university_id, roll_no, department, graduation_year, is_eligible)
SELECT university_id, 'ABC2029ECE001', 'ECE', 2029, 1
FROM universities WHERE slug = 'abc-university';

INSERT INTO students
(university_id, roll_no, department, graduation_year, is_eligible)
SELECT university_id, 'XYZ2029IT001', 'IT', 2029, 1
FROM universities WHERE slug = 'xyz-college';

INSERT INTO students
(university_id, roll_no, department, graduation_year, is_eligible)
SELECT university_id, 'XYZ2029CSE001', 'CSE', 2029, 1
FROM universities WHERE slug = 'xyz-college';

-- 9. Demo placements
INSERT INTO placements
(university_id, student_id, company, role, package_lpa, placement_date, status)
SELECT s.university_id, s.student_id,
       'DemoTech', 'Software Engineer', 7.50, '2026-08-15', 'PLACED'
FROM students s
JOIN universities u ON u.university_id = s.university_id
WHERE s.roll_no = 'ABC2029CSE001'
AND u.slug = 'abc-university';

INSERT INTO placements
(university_id, student_id, company, role, package_lpa, placement_date, status)
SELECT s.university_id, s.student_id,
       'Sample Systems', 'Data Analyst', 6.00, '2026-08-20', 'PLACED'
FROM students s
JOIN universities u ON u.university_id = s.university_id
WHERE s.roll_no = 'XYZ2029IT001'
AND u.slug = 'xyz-college';

-- 10. Verify the setup
SELECT university_id, name, slug
FROM universities
ORDER BY university_id;

SELECT u.slug, COUNT(s.student_id) AS student_count
FROM universities u
LEFT JOIN students s ON s.university_id = u.university_id
GROUP BY u.university_id, u.slug
ORDER BY u.university_id;

SELECT u.slug, COUNT(p.placement_id) AS placement_count
FROM universities u
LEFT JOIN placements p ON p.university_id = u.university_id
GROUP BY u.university_id, u.slug
ORDER BY u.university_id;