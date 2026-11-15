import os
import re
from datetime import date

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for

import database as db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-me')  # needed for flash() messages


@app.template_filter('money')
def money(value):
    return '—' if value is None else f'${int(value):,}'


@app.template_filter('salary_range')
def salary_range(job):
    low, high = job.get('salary_min'), job.get('salary_max')
    if low is None and high is None:
        return '—'
    if low is None or high is None:
        return money(low if low is not None else high)
    return f'{money(low)} – {money(high)}'


@app.template_filter('nice_date')
def nice_date(value):
    if not value:
        return '—'
    return f'{value:%b} {value.day}, {value.year}'


EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^[0-9+()\-.\s]{7,20}$')


def text(field, max_len, errors, label, required=False):
    """Read a text field: strip spaces, check required + length. Blank -> None."""
    value = request.form.get(field, '').strip()
    if required and not value:
        errors[field] = f'{label} is required.'
    elif len(value) > max_len:
        errors[field] = f'{label} must be {max_len} characters or fewer.'
    return value or None


def url_field(field, max_len, errors, label):
    value = text(field, max_len, errors, label)
    if value and not value.lower().startswith(('http://', 'https://')):
        value = 'https://' + value
    if value and '.' not in value:
        errors[field] = f'{label} must be a valid web address.'
    return value


def int_field(field, errors, label, minimum=0, maximum=None):
    raw = request.form.get(field, '').strip().replace(',', '').replace('$', '')
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        errors[field] = f'{label} must be a whole number.'
        return None
    if value < minimum or (maximum is not None and value > maximum):
        errors[field] = f'{label} must be between {minimum} and {maximum}.' if maximum is not None \
            else f'{label} cannot be negative.'
    return value


def date_field(field, errors, label, required=False):
    raw = request.form.get(field, '').strip()
    if not raw:
        if required:
            errors[field] = f'{label} is required.'
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        errors[field] = f'{label} must be a valid date.'
        return None


def choice_field(field, options, errors, label):
    value = request.form.get(field, '')
    if value not in options:
        errors[field] = f'Choose a valid {label.lower()}.'
    return value


def id_field(field, lookup, errors, label):
    """A dropdown that points to another table (foreign key). Make sure the row exists."""
    raw = request.form.get(field, '')
    if not raw.isdigit() or lookup(int(raw)) is None:
        errors[field] = f'Choose a {label.lower()}.'
        return None
    return int(raw)


def get_or_404(row):
    if row is None:
        abort(404)
    return row


def db_error_message(err):
    return f'The database rejected that change: {err.msg}'



@app.route('/')
def dashboard():
    return render_template('dashboard.html', stats=db.get_dashboard_stats())



def read_company_form():
    errors = {}
    values = {
        'company_name': text('company_name', 100, errors, 'Company name', required=True),
        'industry': text('industry', 50, errors, 'Industry'),
        'website': url_field('website', 200, errors, 'Website'),
        'city': text('city', 50, errors, 'City'),
        'state': text('state', 50, errors, 'State'),
        'notes': text('notes', 5000, errors, 'Notes'),
    }
    return values, errors


@app.route('/companies')
def companies():
    return render_template('companies.html', companies=db.get_companies())


@app.route('/companies/<int:company_id>')
def company_detail(company_id):
    company = get_or_404(db.get_company(company_id))
    return render_template('company_detail.html', company=company,
                           jobs=db.get_jobs(company_id=company_id),
                           contacts=db.get_contacts(company_id=company_id))


@app.route('/companies/add', methods=['GET', 'POST'])
def add_company():
    values, errors = {}, {}
    if request.method == 'POST':
        values, errors = read_company_form()
        if not errors:
            try:
                new_id = db.add_company(values['company_name'], values['industry'], values['website'],
                                        values['city'], values['state'], values['notes'])
                flash(f'Added {values["company_name"]}.', 'success')
                return redirect(url_for('company_detail', company_id=new_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return render_template('company_form.html', values=values, errors=errors, company=None)


@app.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    company = get_or_404(db.get_company(company_id))
    values, errors = company, {}
    if request.method == 'POST':
        values, errors = read_company_form()
        if not errors:
            try:
                db.update_company(company_id, values['company_name'], values['industry'], values['website'],
                                  values['city'], values['state'], values['notes'])
                flash(f'Saved changes to {values["company_name"]}.', 'success')
                return redirect(url_for('company_detail', company_id=company_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return render_template('company_form.html', values=values, errors=errors, company=company)


@app.route('/companies/<int:company_id>/delete', methods=['POST'])
def delete_company(company_id):
    company = get_or_404(db.get_company(company_id))
    db.delete_company(company_id)
    flash(f'Deleted {company["company_name"]} and its jobs, applications and contacts.', 'success')
    return redirect(url_for('companies'))



def read_job_form():
    errors = {}
    values = {
        'company_id': id_field('company_id', db.get_company, errors, 'Company'),
        'job_title': text('job_title', 100, errors, 'Job title', required=True),
        'job_type': choice_field('job_type', db.JOB_TYPES, errors, 'Job type'),
        'salary_min': int_field('salary_min', errors, 'Minimum salary', 0, 10_000_000),
        'salary_max': int_field('salary_max', errors, 'Maximum salary', 0, 10_000_000),
        'job_url': url_field('job_url', 300, errors, 'Job posting URL'),
        'date_posted': date_field('date_posted', errors, 'Date posted'),
    }
    if (values['salary_min'] is not None and values['salary_max'] is not None
            and values['salary_max'] < values['salary_min']):
        errors['salary_max'] = 'Maximum salary must be at least the minimum salary.'

    # requirements JSON (same structure as Assignment 7)
    education = text('education', 100, errors, 'Education')
    experience = int_field('experience_years', errors, 'Years of experience', 0, 50)
    requirements = {
        'required_skills': db.split_skills(request.form.get('required_skills')),
        'preferred_skills': db.split_skills(request.form.get('preferred_skills')),
        'education': education,
        'experience_years': experience,
        'remote_option': request.form.get('remote_option') == 'on',
    }
    # leave out empty pieces so the JSON stays clean
    requirements = {k: v for k, v in requirements.items() if v not in (None, [], '')}
    if requirements == {'remote_option': False}:
        requirements = {}
    values['requirements'] = requirements
    return values, errors


def company_options():
    return [(c['company_id'], c['company_name']) for c in db.get_companies()]


def job_form_page(values, errors, job):
    options = company_options()
    return render_template('job_form.html', values=values, errors=errors, job=job,
                           companies=options, company_options=options,
                           type_options=[(t, t) for t in db.JOB_TYPES])


@app.route('/jobs')
def jobs():
    company_id = request.args.get('company_id', type=int)
    job_type = request.args.get('job_type') or None
    search = request.args.get('q', '').strip() or None
    return render_template('jobs.html', jobs=db.get_jobs(company_id, job_type, search),
                           companies=db.get_companies(), job_types=db.JOB_TYPES,
                           filters={'company_id': company_id, 'job_type': job_type, 'q': search or ''})


@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job = get_or_404(db.get_job(job_id))
    return render_template('job_detail.html', job=job, applications=db.get_applications(job_id=job_id))


@app.route('/jobs/add', methods=['GET', 'POST'])
def add_job():
    values = {'company_id': request.args.get('company_id', type=int), 'job_type': 'Full-time',
              'requirements': {}}
    errors = {}
    if request.method == 'POST':
        values, errors = read_job_form()
        if not errors:
            try:
                new_id = db.add_job(values['company_id'], values['job_title'], values['job_type'],
                                    values['salary_min'], values['salary_max'], values['job_url'],
                                    values['date_posted'], values['requirements'])
                flash(f'Added {values["job_title"]}.', 'success')
                return redirect(url_for('job_detail', job_id=new_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return job_form_page(values, errors, None)


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    job = get_or_404(db.get_job(job_id))
    values, errors = job, {}
    if request.method == 'POST':
        values, errors = read_job_form()
        if not errors:
            try:
                db.update_job(job_id, values['company_id'], values['job_title'], values['job_type'],
                              values['salary_min'], values['salary_max'], values['job_url'],
                              values['date_posted'], values['requirements'])
                flash(f'Saved changes to {values["job_title"]}.', 'success')
                return redirect(url_for('job_detail', job_id=job_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return job_form_page(values, errors, job)


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    job = get_or_404(db.get_job(job_id))
    db.delete_job(job_id)
    flash(f'Deleted {job["job_title"]} and its applications.', 'success')
    return redirect(url_for('jobs'))


def read_application_form(existing_interview=None):
    errors = {}
    values = {
        'job_id': id_field('job_id', db.get_job, errors, 'Job'),
        'application_date': date_field('application_date', errors, 'Application date', required=True),
        'status': choice_field('status', db.STATUSES, errors, 'Status'),
        'resume_version': text('resume_version', 50, errors, 'Resume version'),
        'cover_letter_sent': request.form.get('cover_letter_sent') == 'on',
    }
    if values['application_date'] and values['application_date'] > date.today():
        errors['application_date'] = 'Application date cannot be in the future.'

    interview = dict(existing_interview or {})
    updates = {
        'interview_rounds': int_field('interview_rounds', errors, 'Interview rounds', 0, 20),
        'interviewers': db.split_skills(request.form.get('interviewers')),
        'technical_questions': db.split_skills(request.form.get('technical_questions')),
        'feedback': text('feedback', 2000, errors, 'Feedback'),
        'next_steps': text('next_steps', 500, errors, 'Next steps'),
    }
    for key, value in updates.items():
        if value in (None, [], ''):
            interview.pop(key, None)
        else:
            interview[key] = value
    values['interview_data'] = interview
    return values, errors


def application_form_page(values, errors, application):
    job_options = [(j['job_id'], f"{j['job_title']} — {j['company_name']}") for j in db.get_jobs()]
    return render_template('application_form.html', values=values, errors=errors,
                           application=application, job_options=job_options,
                           status_options=[(s, s) for s in db.STATUSES])


@app.route('/applications')
def applications():
    status = request.args.get('status') or None
    if status and status not in db.STATUSES:
        status = None
    return render_template('applications.html', applications=db.get_applications(status=status),
                           statuses=db.STATUSES, current_status=status)


@app.route('/applications/<int:application_id>')
def application_detail(application_id):
    application = get_or_404(db.get_application(application_id))
    return render_template('application_detail.html', application=application)


@app.route('/applications/add', methods=['GET', 'POST'])
def add_application():
    values = {'job_id': request.args.get('job_id', type=int), 'application_date': date.today(),
              'status': 'Applied', 'interview_data': {}}
    errors = {}
    if request.method == 'POST':
        values, errors = read_application_form()
        if not errors:
            try:
                new_id = db.add_application(values['job_id'], values['application_date'], values['status'],
                                            values['resume_version'], values['cover_letter_sent'],
                                            values['interview_data'])
                flash('Application added.', 'success')
                return redirect(url_for('application_detail', application_id=new_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return application_form_page(values, errors, None)


@app.route('/applications/<int:application_id>/edit', methods=['GET', 'POST'])
def edit_application(application_id):
    application = get_or_404(db.get_application(application_id))
    values, errors = application, {}
    if request.method == 'POST':
        values, errors = read_application_form(application['interview_data'])
        if not errors:
            try:
                db.update_application(application_id, values['job_id'], values['application_date'],
                                      values['status'], values['resume_version'],
                                      values['cover_letter_sent'], values['interview_data'])
                flash('Application saved.', 'success')
                return redirect(url_for('application_detail', application_id=application_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return application_form_page(values, errors, application)


@app.route('/applications/<int:application_id>/delete', methods=['POST'])
def delete_application(application_id):
    application = get_or_404(db.get_application(application_id))
    db.delete_application(application_id)
    flash(f'Deleted your application to {application["job_title"]} at {application["company_name"]}.', 'success')
    return redirect(url_for('applications'))


def read_contact_form():
    errors = {}
    values = {
        'company_id': id_field('company_id', db.get_company, errors, 'Company'),
        'contact_name': text('contact_name', 100, errors, 'Name', required=True),
        'title': text('title', 100, errors, 'Title'),
        'email': text('email', 100, errors, 'Email'),
        'phone': text('phone', 20, errors, 'Phone'),
        'linkedin_url': url_field('linkedin_url', 200, errors, 'LinkedIn URL'),
        'notes': text('notes', 5000, errors, 'Notes'),
    }
    if values['email'] and 'email' not in errors and not EMAIL_RE.match(values['email']):
        errors['email'] = 'Enter a valid email address, like name@company.com.'
    if values['phone'] and 'phone' not in errors and not PHONE_RE.match(values['phone']):
        errors['phone'] = 'Phone can only contain numbers, spaces, and + ( ) - .'
    return values, errors


def contact_form_page(values, errors, contact):
    options = company_options()
    return render_template('contact_form.html', values=values, errors=errors, contact=contact,
                           companies=options, company_options=options)


@app.route('/contacts')
def contacts():
    return render_template('contacts.html', contacts=db.get_contacts())


@app.route('/contacts/<int:contact_id>')
def contact_detail(contact_id):
    contact = get_or_404(db.get_contact(contact_id))
    return render_template('contact_detail.html', contact=contact)


@app.route('/contacts/add', methods=['GET', 'POST'])
def add_contact():
    values = {'company_id': request.args.get('company_id', type=int)}
    errors = {}
    if request.method == 'POST':
        values, errors = read_contact_form()
        if not errors:
            try:
                new_id = db.add_contact(values['company_id'], values['contact_name'], values['title'],
                                        values['email'], values['phone'], values['linkedin_url'],
                                        values['notes'])
                flash(f'Added {values["contact_name"]}.', 'success')
                return redirect(url_for('contact_detail', contact_id=new_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return contact_form_page(values, errors, None)


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    contact = get_or_404(db.get_contact(contact_id))
    values, errors = contact, {}
    if request.method == 'POST':
        values, errors = read_contact_form()
        if not errors:
            try:
                db.update_contact(contact_id, values['company_id'], values['contact_name'], values['title'],
                                  values['email'], values['phone'], values['linkedin_url'], values['notes'])
                flash(f'Saved changes to {values["contact_name"]}.', 'success')
                return redirect(url_for('contact_detail', contact_id=contact_id))
            except mysql.connector.Error as err:
                flash(db_error_message(err), 'error')
    return contact_form_page(values, errors, contact)


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    contact = get_or_404(db.get_contact(contact_id))
    db.delete_contact(contact_id)
    flash(f'Deleted {contact["contact_name"]}.', 'success')
    return redirect(url_for('contacts'))



@app.route('/job-match')
def job_match():
    skills_text = request.args.get('skills', '').strip()
    results = db.match_jobs(skills_text) if skills_text else None
    show_all = request.args.get('show') == 'all'
    if results is not None and not show_all:
        hidden = sum(1 for r in results if r['percent'] == 0)
        results = [r for r in results if r['percent'] > 0]
    else:
        hidden = 0
    return render_template('job_match.html', skills_text=skills_text,
                           skills=db.split_skills(skills_text), results=results,
                           hidden=hidden, show_all=show_all)


@app.errorhandler(404)
def not_found(_error):
    return render_template('not_found.html'), 404


@app.errorhandler(mysql.connector.Error)
def database_down(err):
    return render_template('db_error.html', error=err), 500


if __name__ == '__main__':
    app.run(debug=True)
