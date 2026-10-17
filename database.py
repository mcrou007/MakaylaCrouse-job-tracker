import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'job_tracker',
}


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


# ---------- companies ----------
def get_companies():
    return query('SELECT * FROM companies ORDER BY company_name')


# Quick test: run "python database.py"
if __name__ == '__main__':
    companies = get_companies()
    print(f'Connected! Found {len(companies)} companies:')
    for c in companies:
        print(' -', c['company_name'])