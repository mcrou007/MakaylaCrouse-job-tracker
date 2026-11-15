-- =====================================================================
-- schema.sql — Job Application Tracker

DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;


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


CREATE INDEX idx_company_industry ON companies(industry);
CREATE INDEX idx_job_title        ON jobs(job_title);
CREATE INDEX idx_company_type     ON jobs(company_id, job_type);
CREATE INDEX idx_app_status       ON applications(status);


INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Solutions Inc',  'Technology',      'https://www.techsolutions.com',      'Miami',         'Florida',       'Local company, hybrid schedule.'),
('Data Analytics Corp', 'Data Science',    'https://www.dataanalytics.com',      'Austin',        'Texas',         NULL),
('Cloud Systems LLC',   'Cloud Computing', 'https://www.cloudsystems.com',       'Seattle',       'Washington',    'Fully remote option.'),
('Digital Innovations', 'Software',        'https://www.digitalinnovations.com', 'San Francisco', 'California',    NULL),
('Smart Tech Group',    'AI/ML',           'https://www.smarttech.com',          'Boston',        'Massachusetts', 'Met recruiter at career fair.');

-- requirements follows the structure from Assignment 7.
-- Job Match compares your skills against required_skills.
INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 70000, 90000, 'https://www.techsolutions.com/careers/101', '2025-01-15',
    '{"required_skills": ["Python", "SQL", "Git"], "preferred_skills": ["Flask", "Docker", "AWS"], "education": "Bachelor in CS or related field", "experience_years": 2, "remote_option": true}'),
(1, 'Database Administrator', 'Full-time', 75000, 95000, 'https://www.techsolutions.com/careers/102', '2025-01-10',
    '{"required_skills": ["SQL", "MySQL", "Linux"], "preferred_skills": ["Backup and Recovery", "Python"], "education": "Bachelor in CS or related field", "experience_years": 3, "remote_option": false}'),
(1, 'Technical Writer', 'Contract', 55000, 75000, NULL, '2025-01-12',
    '{"required_skills": ["Writing", "Markdown"], "preferred_skills": ["Git"], "education": "Bachelor degree", "experience_years": 1, "remote_option": true}'),
(2, 'Data Analyst', 'Full-time', 65000, 85000, 'https://www.dataanalytics.com/jobs/data-analyst', '2025-01-12',
    '{"required_skills": ["SQL", "Excel", "Tableau"], "preferred_skills": ["Python", "R"], "education": "Bachelor degree", "experience_years": 1, "remote_option": false}'),
(2, 'Data Scientist', 'Full-time', 85000, 110000, NULL, '2025-01-07',
    '{"required_skills": ["Python", "SQL", "Machine Learning", "Statistics"], "preferred_skills": ["R", "Tableau"], "education": "Master in Data Science or related field", "experience_years": 3, "remote_option": true}'),
(2, 'Intern - Data', 'Internship', 30000, 40000, NULL, '2025-01-13',
    '{"required_skills": ["Excel", "SQL"], "preferred_skills": ["Python"], "education": "Currently enrolled in college", "experience_years": 0, "remote_option": false}'),
(3, 'Cloud Engineer', 'Full-time', 80000, 100000, 'https://www.cloudsystems.com/jobs/cloud-eng', '2025-01-08',
    '{"required_skills": ["AWS", "Linux", "Python"], "preferred_skills": ["Docker", "Terraform"], "education": "Bachelor in CS or related field", "experience_years": 3, "remote_option": true}'),
(3, 'DevOps Engineer', 'Full-time', 80000, 105000, NULL, '2025-01-08',
    '{"required_skills": ["Docker", "Kubernetes", "Linux", "Git"], "preferred_skills": ["AWS", "Python"], "education": "Bachelor in CS or related field", "experience_years": 3, "remote_option": true}'),
(4, 'Junior Developer', 'Full-time', 55000, 70000, NULL, '2025-01-14',
    '{"required_skills": ["JavaScript", "HTML", "CSS"], "preferred_skills": ["Git", "React"], "education": "Bachelor degree", "experience_years": 0, "remote_option": false}'),
(4, 'Senior Developer', 'Full-time', 95000, 120000, NULL, '2025-01-14',
    '{"required_skills": ["Python", "JavaScript", "SQL"], "preferred_skills": ["System Design", "AWS"], "education": "Bachelor in CS or related field", "experience_years": 5, "remote_option": true}'),
(4, 'Intern - Development', 'Part-time', 32000, 42000, NULL, '2025-01-14',
    '{"required_skills": ["Python", "HTML", "CSS"], "preferred_skills": ["Flask", "Git"], "education": "Currently enrolled in college", "experience_years": 0, "remote_option": false}'),
(5, 'ML Engineer', 'Full-time', 90000, 115000, 'https://www.smarttech.com/careers/ml-engineer', '2025-01-11',
    '{"required_skills": ["Python", "Machine Learning", "SQL"], "preferred_skills": ["TensorFlow", "Docker"], "education": "Master in CS or related field", "experience_years": 3, "remote_option": true}');

-- interview_data follows the structure from Assignment 7.
INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2025-01-16', 'Interview', 'v2.1', TRUE,
    '{"interview_rounds": 2, "interviewers": ["Sarah Johnson", "Mike Chen"], "technical_questions": ["SQL joins", "Python basics", "API design"], "feedback": "Strong technical skills, good communication", "next_steps": "Final round scheduled"}'),
(4, '2025-01-13', 'Screening', 'v2.1', TRUE,
    '{"interview_rounds": 1, "interviewers": ["Michael Chen"], "technical_questions": ["Excel pivot tables"], "feedback": "Friendly phone screen", "next_steps": "Waiting to hear back"}'),
(7, '2025-01-09', 'Rejected', 'v2.0', FALSE,
    '{"interview_rounds": 1, "interviewers": ["Emily Williams"], "technical_questions": ["Database normalization", "Transaction isolation"], "feedback": "Needs more experience with cloud platforms"}'),
(9, '2025-01-15', 'Applied', 'v2.1', TRUE,
    NULL),
(12, '2025-01-12', 'Offer', 'v2.1', TRUE,
    '{"interview_rounds": 3, "interviewers": ["Lisa Garcia"], "technical_questions": ["Model evaluation", "Python data structures"], "feedback": "Great culture fit", "next_steps": "Offer extended!"}'),
(11, '2025-01-18', 'Withdrawn', 'v2.2', FALSE,
    NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson',   'HR Manager',          'sjohnson@techsolutions.com', '305-555-0101', 'https://www.linkedin.com/in/sarahjohnson', 'Scheduled my technical interview.'),
(2, 'Michael Chen',    'Technical Recruiter', 'mchen@dataanalytics.com',    NULL,           NULL,                                       NULL),
(3, 'Emily Williams',  'Hiring Manager',      'ewilliams@cloudsystems.com', '206-555-0144', NULL,                                       NULL),
(4, 'David Brown',     'Senior Developer',    NULL,                         NULL,           'https://www.linkedin.com/in/davidbrown',   'Referral contact.'),
(4, 'Robert Kim',      'Engineering Manager', 'rkim@digitalinnovations.com', NULL,          NULL,                                       NULL),
(5, 'Lisa Garcia',     'Talent Acquisition',  'lgarcia@smarttech.com',      '617-555-0199', NULL,                                       'Met at FIU career fair.');
