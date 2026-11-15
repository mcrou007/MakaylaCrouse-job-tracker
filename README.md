# Job Application Tracker

A web app for tracking a job search: the companies you're interested in, their job postings, your applications, and the people you've talked to. It also has a **Job Match** page that ranks jobs by how many of their required skills you already have.

Built with **MySQL**, **Python 3 + Flask**, and **HTML/CSS**.

## Features

- **Dashboard**: totals for each table, applications by status, response rate, jobs by company, average salary by industry, and recent applications
- **Companies, Jobs, Applications, Contacts**: full CRUD for all four tables (list, detail view, add, edit, delete with confirmation)
- **Validation**: required fields, salary min ≤ max, valid dates, emails, phone numbers and URLs, and dropdowns that only accept real companies/jobs
- **Filters**: search jobs by title, company and type; filter applications by status
- **JSON columns**: `jobs.requirements` (skills, education, experience, remote option) and `applications.interview_data` (rounds, interviewers, questions, feedback, next steps)
- **Job Match**: enter your skills and see jobs ranked by match percentage, with the skills you have and the ones you're missing

## Project structure

```
job-tracker/
├── app.py              # Flask routes (pages, forms, validation)
├── database.py         # All MySQL queries (parameterized with %s)
├── schema.sql          # Creates the job_tracker database, tables, indexes and sample data
├── requirements.txt    # Python packages
├── .env.example        # Template for your .env file (database password)
├── templates/          # HTML pages (Jinja templates)
│   ├── base.html       # Shared layout and navigation
│   ├── _macros.html    # Reusable form fields and buttons
│   ├── dashboard.html
│   ├── companies.html, company_detail.html, company_form.html
│   ├── jobs.html, job_detail.html, job_form.html
│   ├── applications.html, application_detail.html, application_form.html
│   ├── contacts.html, contact_detail.html, contact_form.html
│   └── job_match.html
├── static/
│   └── style.css
├── AI_USAGE.md         # How AI tools were used
└── README.md
```

## Setup

### 1. Install the prerequisites

- **MySQL Server 8.0+** and **MySQL Workbench**: https://dev.mysql.com/downloads/
- **Python 3.10+**: https://www.python.org/downloads/ (on Windows, check **"Add Python to PATH"** during install)

### 2. Get the code

```
git clone <this repository's URL>
cd job-tracker
```

### 3. Install the Python packages

```
python -m pip install -r requirements.txt
```

### 4. Create the database

Open MySQL Workbench, connect to your local server, then go to **File → Open SQL Script**, choose `schema.sql`, and click the lightning bolt to run it.

Or from a terminal:

```
mysql -u root -p < schema.sql
```

This creates the `job_tracker` database with all four tables and sample data.

> ⚠️ `schema.sql` drops and recreates `job_tracker`, so running it again resets the data.

### 5. Add your MySQL password

Make a copy of `.env.example` named `.env` in the project folder, and put your MySQL root password in it:

```
DB_PASSWORD=your_mysql_root_password
```

### 6. Run the app

```
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. Press `Ctrl + C` in the terminal to stop the server.

To check only the database connection, run `python database.py`. It should print `Connected! Found 5 companies`.

## Troubleshooting

| Error | Fix |
|---|---|
| `'pip' is not recognized` | Use `python -m pip install -r requirements.txt` (or `py -m pip ...`). |
| `'python' is not recognized` | Try `py app.py`, or reinstall Python with "Add Python to PATH" checked. |
| `Access denied for user 'root'@'localhost'` | The password in `.env` is wrong. Use the one you type in MySQL Workbench. |
| `Unknown database 'job_tracker'` | Run `schema.sql` (step 4). |
| `ModuleNotFoundError: No module named 'flask'` | Run step 3 again. |

## Database design

Four tables, all using the InnoDB engine:

| Table | Key columns | Relationship |
|---|---|---|
| `companies` | `company_id` (PK), `company_name` | One company has many jobs and many contacts |
| `jobs` | `job_id` (PK), `company_id` (FK), `job_type` ENUM, `requirements` JSON | One job has many applications |
| `applications` | `application_id` (PK), `job_id` (FK), `status` ENUM, `interview_data` JSON | |
| `contacts` | `contact_id` (PK), `company_id` (FK), `contact_name` | |

- **Foreign keys** use `ON DELETE CASCADE`. Deleting a company also deletes its jobs, their applications and its contacts, and the app warns you before it does this.
- **A CHECK constraint** stops a job from having `salary_max` lower than `salary_min`.
- **ENUM columns** restrict `job_type` and `status` to the allowed values.
- **Indexes** on `companies.industry`, `jobs.job_title`, `jobs(company_id, job_type)` and `applications.status` speed up the searches and filters.

### JSON columns

`jobs.requirements`:
```json
{"required_skills": ["Python", "SQL", "Git"], "preferred_skills": ["Flask", "Docker"],
 "education": "Bachelor in CS or related field", "experience_years": 2, "remote_option": true}
```

`applications.interview_data`:
```json
{"interview_rounds": 2, "interviewers": ["Sarah Johnson", "Mike Chen"],
 "technical_questions": ["SQL joins", "API design"],
 "feedback": "Strong technical skills", "next_steps": "Final round scheduled"}
```

They can be queried with MySQL's JSON functions, for example:
```sql
SELECT job_title FROM jobs WHERE JSON_CONTAINS(requirements->'$.required_skills', '"Python"');
```

## How Job Match works

1. You type your skills, separated by commas (`Python, SQL, Flask`).
2. For every job, the app reads `required_skills` from the `requirements` JSON.
3. **Match % = required skills you have ÷ total required skills.** Matching ignores capital letters, so `python` matches `Python`.
4. Jobs are sorted by match %, then by number of matching skills. Each result shows the skills you have, the ones you're missing, and any preferred skills you also have.

Example: with `Python, SQL, Flask`, **Software Developer** (needs Python, SQL, Git) is a **67%** match, and Git is shown as missing.

## Demo video

A video of the app running (browser, Flask server, and MySQL Workbench) is in this repository: `demo_video.mp4`
