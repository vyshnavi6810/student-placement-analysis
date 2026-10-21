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



