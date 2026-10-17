-- =====================================================================
-- schema.sql — Job Application Tracker
-- Creates the job_tracker database, all 4 tables, indexes, and sample data.
-- Run in MySQL Workbench (File > Open SQL Script > lightning bolt)
-- or from a terminal:  mysql -u root -p < schema.sql
-- WARNING: this drops and recreates job_tracker, erasing existing data.
-- =====================================================================

DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

-- ---------------------------------------------------------------------
-- companies
-- ---------------------------------------------------------------------
CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- jobs  (requirements = JSON array of skills, used by Job Match)
-- ---------------------------------------------------------------------
CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship') DEFAULT 'Full-time',
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_salary_range
        CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min)
);

-- ---------------------------------------------------------------------
-- applications  (interview_data = JSON object with interview details)
-- ---------------------------------------------------------------------
CREATE TABLE applications (
    application_id    INT PRIMARY KEY AUTO_INCREMENT,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn')
                      DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data    JSON,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- contacts
-- ---------------------------------------------------------------------
CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Indexes (from Assignment 3) for common searches
-- ---------------------------------------------------------------------
CREATE INDEX idx_company_industry ON companies(industry);
CREATE INDEX idx_job_title        ON jobs(job_title);
CREATE INDEX idx_company_type     ON jobs(company_id, job_type);
CREATE INDEX idx_app_status       ON applications(status);

-- ---------------------------------------------------------------------
-- Sample data
-- ---------------------------------------------------------------------
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Solutions Inc',  'Technology',      'https://www.techsolutions.com',      'Miami',         'Florida',       'Local company, hybrid schedule.'),
('Data Analytics Corp', 'Data Science',    'https://www.dataanalytics.com',      'Austin',        'Texas',         NULL),
('Cloud Systems LLC',   'Cloud Computing', 'https://www.cloudsystems.com',       'Seattle',       'Washington',    'Fully remote option.'),
('Digital Innovations', 'Software',        'https://www.digitalinnovations.com', 'San Francisco', 'California',    NULL),
('Smart Tech Group',    'AI/ML',           'https://www.smarttech.com',          'Boston',        'Massachusetts', 'Met recruiter at career fair.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer',     'Full-time',  70000,  90000, 'https://www.techsolutions.com/careers/101',      '2025-01-15', '["Python", "SQL", "Flask", "Git"]'),
(1, 'Database Administrator', 'Full-time',  75000,  95000, 'https://www.techsolutions.com/careers/102',      '2025-01-10', '["SQL", "MySQL", "Linux", "Backup and Recovery"]'),
(1, 'Technical Writer',       'Contract',   55000,  75000, NULL,                                            '2025-01-12', '["Writing", "Markdown", "Git"]'),
(2, 'Data Analyst',           'Full-time',  65000,  85000, 'https://www.dataanalytics.com/jobs/data-analyst', '2025-01-12', '["SQL", "Python", "Excel", "Tableau"]'),
(2, 'Data Scientist',         'Full-time',  85000, 110000, NULL,                                            '2025-01-07', '["Python", "SQL", "Machine Learning", "Statistics"]'),
(2, 'Intern - Data',          'Internship', 30000,  40000, NULL,                                            '2025-01-13', '["Excel", "SQL"]'),
(3, 'Cloud Engineer',         'Full-time',  80000, 100000, 'https://www.cloudsystems.com/jobs/cloud-eng',    '2025-01-08', '["AWS", "Linux", "Python", "Docker"]'),
(3, 'DevOps Engineer',        'Full-time',  80000, 105000, NULL,                                            '2025-01-08', '["Docker", "Kubernetes", "Linux", "Git"]'),
(4, 'Junior Developer',       'Full-time',  55000,  70000, NULL,                                            '2025-01-14', '["JavaScript", "HTML", "CSS", "Git"]'),
(4, 'Senior Developer',       'Full-time',  95000, 120000, NULL,                                            '2025-01-14', '["Python", "JavaScript", "SQL", "System Design"]'),
(4, 'Intern - Development',   'Part-time',  32000,  42000, NULL,                                            '2025-01-14', '["Python", "HTML", "CSS"]'),
(5, 'ML Engineer',            'Full-time',  90000, 115000, 'https://www.smarttech.com/careers/ml-engineer',  '2025-01-11', '["Python", "Machine Learning", "TensorFlow", "SQL"]');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1,  '2025-01-16', 'Interview', 'v2.1', TRUE,
     '{"round": 2, "type": "Technical", "date": "2025-01-28 14:00", "interviewer": "Sarah Johnson", "notes": "Live coding in Python"}'),
(4,  '2025-01-13', 'Screening', 'v2.1', TRUE,
     '{"round": 1, "type": "Phone", "date": "2025-01-20 10:30", "interviewer": "Michael Chen"}'),
(7,  '2025-01-09', 'Rejected',  'v2.0', FALSE, NULL),
(9,  '2025-01-15', 'Applied',   'v2.1', TRUE,  NULL),
(12, '2025-01-12', 'Offer',     'v2.1', TRUE,
     '{"round": 3, "type": "Final", "date": "2025-01-24 13:00", "interviewer": "Lisa Garcia", "notes": "Offer received 2025-01-30"}'),
(11, '2025-01-18', 'Withdrawn', 'v2.2', FALSE, NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson',   'HR Manager',          'sjohnson@techsolutions.com', '305-555-0101', 'https://www.linkedin.com/in/sarahjohnson', 'Scheduled my technical interview.'),
(2, 'Michael Chen',    'Technical Recruiter', 'mchen@dataanalytics.com',    NULL,           NULL,                                       NULL),
(3, 'Emily Williams',  'Hiring Manager',      'ewilliams@cloudsystems.com', '206-555-0144', NULL,                                       NULL),
(4, 'David Brown',     'Senior Developer',    NULL,                         NULL,           'https://www.linkedin.com/in/davidbrown',   'Referral contact.'),
(4, 'Robert Kim',      'Engineering Manager', 'rkim@digitalinnovations.com', NULL,          NULL,                                       NULL),
(5, 'Lisa Garcia',     'Talent Acquisition',  'lgarcia@smarttech.com',      '617-555-0199', NULL,                                       'Met at FIU career fair.');
