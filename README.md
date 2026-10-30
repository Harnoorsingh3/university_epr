# University ERP — Flask + SQLite

A runnable **educational university ERP starter system** with role-based logins, a responsive interface, SQLite database, and administrative records.

**Repository:** https://github.com/Harnoorsingh3/university_epr

> This is a local development MVP, not a production-ready college ERP. Do not store real sensitive student data or payment details until the software has been independently security-reviewed and hardened.

## Implemented modules

| Admin | Faculty | Student |
|---|---|---|
| Departments, students, faculty, courses, enrollments | Own assigned courses and enrollments | Own profile and courses |
| Attendance and grade entry | Attendance and grade entry for own courses | Own attendance and grades |
| Fee records, timetable, announcements | Own timetable and announcements | Own fee records, timetable, announcements |
| Library books and loans; hostel rooms and allocations | — | Own library loans and hostel allocation |
| Helpdesk tickets, user accounts, dashboard counts | — | Create and view own tickets |

The app has password-hashed accounts, session login, CSRF tokens, SQL parameters, foreign keys, basic database validation and audit entries for writes. It does **not** yet include actual payment collection, admissions workflow, exam engine, notifications, transcript generation, account suspension UI, or production-level security.

## Run locally

Requires **Python 3.10+**.

```bash
git clone https://github.com/Harnoorsingh3/university_epr.git
cd university_epr
python -m venv .venv
```

Activate your environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

Then:

```bash
python -m pip install -r requirements.txt
flask --app app init-db
flask --app app init-admin
flask --app app run
```

The admin creation command asks for a username and password of **at least 12 characters**. There is no default login. Open **http://127.0.0.1:5000** in your browser.

For consistent sessions set a long, random `SECRET_KEY` environment variable before starting Flask:

- Windows PowerShell: `$env:SECRET_KEY="replace-with-long-random-secret"`
- macOS/Linux: `export SECRET_KEY="replace-with-long-random-secret"`

## First-time setup

1. Sign in as administrator.
2. Add **departments**, then **students** and **faculty**. Use IDs from the departments table.
3. Create **courses**; link a faculty member and department by ID.
4. Create **enrollments** linking students to courses.
5. Add fees, timetable sessions, announcements, library catalog/loans, and hostel records.
6. Under **Accounts**, create student/faculty login accounts linked to their record IDs.
7. Faculty record attendance or grades by enrollment ID. Students see only their own records and can open helpdesk tickets.

Attendance values are `present`, `absent`, `late`; grades use nonnegative score and positive maximum. The basic entry screens use IDs rather than dropdowns; look up valid IDs in each module before adding related records.

## Automated checks

```bash
python -m pytest -q
```

Tests in `tests/test_app.py` cover login, dashboard, student fee isolation, role restrictions, CSRF protection and admin creation of a department.

## Project structure

```text
university_epr/
  app.py
  schema.sql
  static/style.css
  tests/test_app.py
  requirements.txt
  .gitignore
  README.md
```

## Security and future work

SQLite lives inside the ignored `instance/` folder. Passwords are stored using Werkzeug hashes. Student/faculty queries are scoped by signed-in user. Forms protect against CSRF; use HTTPS and `COOKIE_SECURE=1` for any secure deployment.

Still needed before real use: login throttling, password reset and verification, comprehensive input validation, user account management, backup and recovery, data retention and privacy compliance, database migrations, pagination, accessibility review, stronger logging, transactional fee processing, security testing and proper production hosting.

**Stack:** Python, Flask, SQLite, HTML/CSS, Werkzeug, pytest.
