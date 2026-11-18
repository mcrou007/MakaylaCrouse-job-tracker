"""
database.py - all MySQL access for the Job Application Tracker.

Every function opens a connection, runs one statement with %s placeholders
(parameterized queries prevent SQL injection), and closes the connection.
"""
import json
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'job_tracker'),
}

JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']
STATUSES = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn']


def get_connection():
    return mysql.connector.connect(**CONFIG)


def query(sql, params=(), fetch=True):
    """Run one SQL statement.
    fetch=True  -> returns a list of rows (as dictionaries)
    fetch=False -> commits and returns the new row's id (for INSERT/UPDATE/DELETE)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


# ---------- JSON helpers ----------
def parse_json(value):
    """MySQL JSON columns come back as text; turn them into Python dicts/lists."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode('utf-8')
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def parse_requirements(value):
    """Always return requirements as a dict like {'required_skills': [...], ...}.
    Older data stored it as a plain list of skills, e.g. ["Python", "SQL"],
    so a list is treated as the required skills."""
    data = parse_json(value)
    if isinstance(data, list):
        return {'required_skills': [str(s) for s in data]}
    if isinstance(data, dict):
        return data
    return {}


def _with_json(rows, column):
    for row in rows:
        row[column] = parse_json(row.get(column)) or {}
    return rows


# =====================================================================
# companies
# =====================================================================
def get_companies():
    return query('''
        SELECT c.*,
               (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id) AS job_count,
               (SELECT COUNT(*) FROM contacts ct WHERE ct.company_id = c.company_id) AS contact_count
        FROM companies c
        ORDER BY c.company_name''')


def get_company(company_id):
    return query_one('SELECT * FROM companies WHERE company_id = %s', (company_id,))


def add_company(name, industry, website, city, state, notes):
    return query(
        '''INSERT INTO companies (company_name, industry, website, city, state, notes)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (name, industry, website, city, state, notes), fetch=False)


def update_company(company_id, name, industry, website, city, state, notes):
    query(
        '''UPDATE companies
           SET company_name=%s, industry=%s, website=%s, city=%s, state=%s, notes=%s
           WHERE company_id=%s''',
        (name, industry, website, city, state, notes, company_id), fetch=False)


def delete_company(company_id):
    # ON DELETE CASCADE in schema.sql also removes this company's jobs,
    # their applications, and the company's contacts.
    query('DELETE FROM companies WHERE company_id = %s', (company_id,), fetch=False)


# =====================================================================
# jobs  (requirements is a JSON column)
# =====================================================================
JOB_SELECT = '''
    SELECT j.*, c.company_name,
           (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
    FROM jobs j
    JOIN companies c ON j.company_id = c.company_id'''


def get_jobs(company_id=None, job_type=None, search=None):
    sql = JOB_SELECT + ' WHERE 1=1'
    params = []
    if company_id:
        sql += ' AND j.company_id = %s'
        params.append(company_id)
    if job_type:
        sql += ' AND j.job_type = %s'
        params.append(job_type)
    if search:
        sql += ' AND j.job_title LIKE %s'
        params.append(f'%{search}%')
    sql += ' ORDER BY j.date_posted DESC, j.job_title'
    rows = query(sql, tuple(params))
    for row in rows:
        row['requirements'] = parse_requirements(row.get('requirements'))
    return rows


def get_job(job_id):
    row = query_one(JOB_SELECT + ' WHERE j.job_id = %s', (job_id,))
    if row:
        row['requirements'] = parse_requirements(row['requirements'])
    return row


def add_job(company_id, title, job_type, salary_min, salary_max, job_url, date_posted, requirements):
    return query(
        '''INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                             job_url, date_posted, requirements)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
        (company_id, title, job_type, salary_min, salary_max, job_url, date_posted,
         json.dumps(requirements) if requirements else None), fetch=False)


def update_job(job_id, company_id, title, job_type, salary_min, salary_max, job_url, date_posted, requirements):
    query(
        '''UPDATE jobs
           SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s, salary_max=%s,
               job_url=%s, date_posted=%s, requirements=%s
           WHERE job_id=%s''',
        (company_id, title, job_type, salary_min, salary_max, job_url, date_posted,
         json.dumps(requirements) if requirements else None, job_id), fetch=False)


def delete_job(job_id):
    query('DELETE FROM jobs WHERE job_id = %s', (job_id,), fetch=False)


# =====================================================================
# applications  (interview_data is a JSON column)
# =====================================================================
APP_SELECT = '''
    SELECT a.*, j.job_title, j.company_id, c.company_name
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    JOIN companies c ON j.company_id = c.company_id'''


def get_applications(status=None, job_id=None):
    sql = APP_SELECT + ' WHERE 1=1'
    params = []
    if status:
        sql += ' AND a.status = %s'
        params.append(status)
    if job_id:
        sql += ' AND a.job_id = %s'
        params.append(job_id)
    sql += ' ORDER BY a.application_date DESC, a.application_id DESC'
    return _with_json(query(sql, tuple(params)), 'interview_data')


def get_application(application_id):
    row = query_one(APP_SELECT + ' WHERE a.application_id = %s', (application_id,))
    if row:
        row['interview_data'] = parse_json(row['interview_data']) or {}
    return row


def add_application(job_id, application_date, status, resume_version, cover_letter_sent, interview_data):
    return query(
        '''INSERT INTO applications (job_id, application_date, status, resume_version,
                                     cover_letter_sent, interview_data)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (job_id, application_date, status, resume_version, cover_letter_sent,
         json.dumps(interview_data) if interview_data else None), fetch=False)


def update_application(application_id, job_id, application_date, status, resume_version,
                       cover_letter_sent, interview_data):
    query(
        '''UPDATE applications
           SET job_id=%s, application_date=%s, status=%s, resume_version=%s,
               cover_letter_sent=%s, interview_data=%s
           WHERE application_id=%s''',
        (job_id, application_date, status, resume_version, cover_letter_sent,
         json.dumps(interview_data) if interview_data else None, application_id), fetch=False)


def delete_application(application_id):
    query('DELETE FROM applications WHERE application_id = %s', (application_id,), fetch=False)


# =====================================================================
# contacts
# =====================================================================
CONTACT_SELECT = '''
    SELECT ct.*, c.company_name
    FROM contacts ct
    JOIN companies c ON ct.company_id = c.company_id'''


def get_contacts(company_id=None):
    if company_id:
        return query(CONTACT_SELECT + ' WHERE ct.company_id = %s ORDER BY ct.contact_name', (company_id,))
    return query(CONTACT_SELECT + ' ORDER BY c.company_name, ct.contact_name')


def get_contact(contact_id):
    return query_one(CONTACT_SELECT + ' WHERE ct.contact_id = %s', (contact_id,))


def add_contact(company_id, name, title, email, phone, linkedin_url, notes):
    return query(
        '''INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (company_id, name, title, email, phone, linkedin_url, notes), fetch=False)


def update_contact(contact_id, company_id, name, title, email, phone, linkedin_url, notes):
    query(
        '''UPDATE contacts
           SET company_id=%s, contact_name=%s, title=%s, email=%s, phone=%s,
               linkedin_url=%s, notes=%s
           WHERE contact_id=%s''',
        (company_id, name, title, email, phone, linkedin_url, notes, contact_id), fetch=False)


def delete_contact(contact_id):
    query('DELETE FROM contacts WHERE contact_id = %s', (contact_id,), fetch=False)


# =====================================================================
# dashboard statistics (analytical queries from Assignment 6)
# =====================================================================
def get_dashboard_stats():
    counts = query_one('''
        SELECT (SELECT COUNT(*) FROM companies)    AS companies,
               (SELECT COUNT(*) FROM jobs)         AS jobs,
               (SELECT COUNT(*) FROM applications) AS applications,
               (SELECT COUNT(*) FROM contacts)     AS contacts''')

    by_status = {row['status']: row['count'] for row in query(
        'SELECT status, COUNT(*) AS count FROM applications GROUP BY status')}
    status_counts = [{'status': s, 'count': by_status.get(s, 0)} for s in STATUSES]

    response = query_one('''
        SELECT COUNT(*) AS total,
               COALESCE(SUM(CASE WHEN status != 'Applied' THEN 1 ELSE 0 END), 0) AS responded
        FROM applications''')
    response_rate = round(response['responded'] * 100 / response['total']) if response['total'] else 0

    jobs_by_company = query('''
        SELECT c.company_id, c.company_name, COUNT(j.job_id) AS job_count
        FROM companies c
        LEFT JOIN jobs j ON c.company_id = j.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY job_count DESC, c.company_name
        LIMIT 6''')

    salary_by_industry = query('''
        SELECT c.industry,
               ROUND(AVG(j.salary_min), 0) AS avg_min,
               ROUND(AVG(j.salary_max), 0) AS avg_max
        FROM companies c
        JOIN jobs j ON c.company_id = j.company_id
        WHERE j.salary_min IS NOT NULL AND c.industry IS NOT NULL
        GROUP BY c.industry
        ORDER BY avg_max DESC''')

    recent = query(APP_SELECT + ' ORDER BY a.application_date DESC, a.application_id DESC LIMIT 5')

    return {
        'counts': counts,
        'status_counts': status_counts,
        'response_rate': response_rate,
        'responded': int(response['responded']),
        'total_applications': response['total'],
        'jobs_by_company': jobs_by_company,
        'salary_by_industry': salary_by_industry,
        'recent': recent,
    }


# =====================================================================
# Job Match
# =====================================================================
def split_skills(text):
    """'Python, SQL,  flask' -> ['Python', 'SQL', 'flask'] (no blanks, no duplicates)."""
    skills = []
    seen = set()
    for part in (text or '').split(','):
        skill = part.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def match_jobs(skills_text):
    """Rank every job by the % of its required_skills that the user has."""
    mine = {s.lower() for s in split_skills(skills_text)}
    results = []
    for job in get_jobs():
        required = job['requirements'].get('required_skills', [])
        if not required:
            continue
        matched = [s for s in required if s.lower() in mine]
        missing = [s for s in required if s.lower() not in mine]
        preferred = job['requirements'].get('preferred_skills', [])
        results.append({
            **job,
            'percent': round(len(matched) * 100 / len(required)),
            'matched': matched,
            'missing': missing,
            'total': len(required),
            'preferred_matched': [s for s in preferred if s.lower() in mine],
        })
    results.sort(key=lambda r: (-r['percent'], -len(r['matched']), -len(r['preferred_matched']), r['job_title']))
    return results


# Quick test: run "python database.py"
if __name__ == '__main__':
    companies = get_companies()
    print(f'Connected! Found {len(companies)} companies:')
    for c in companies:
        print(' -', c['company_name'])
