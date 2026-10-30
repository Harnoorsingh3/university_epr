# University ERP — latest automated execution

**Source:** GitHub Actions run [#1](https://github.com/Harnoorsingh3/university_epr/actions/runs/41138644463)

**Automated test step:** success

**Application demo step:** success

## Pytest output
~~~text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.12.15/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/university_epr/university_epr
collecting ... collected 5 items

tests/test_app.py::test_login_and_dashboard PASSED                       [ 20%]
tests/test_app.py::test_student_fee_isolation PASSED                     [ 40%]
tests/test_app.py::test_student_forbidden_admin_accounts PASSED          [ 60%]
tests/test_app.py::test_csrf_rejects_unprotected_write PASSED            [ 80%]
tests/test_app.py::test_admin_can_create_department PASSED               [100%]

============================== 5 passed in 1.91s ===============================
~~~

## Demo application output
~~~text
UNIVERSITY ERP — DEMO OUTPUT
Login page: HTTP 200
Admin login / dashboard: HTTP 200
departments: HTTP 200
students: HTTP 200
faculty: HTTP 200
courses: HTTP 200
enrollments: HTTP 200
attendance: HTTP 200
grades: HTTP 200
fees: HTTP 200
announcements: HTTP 200
timetable: HTTP 200
library_books: HTTP 200
hostel_rooms: HTTP 200
tickets: HTTP 200
Student login / dashboard: HTTP 200
Student sees own fee record: PASS
Student blocked from admin accounts: HTTP 403
ALL DEMO CHECKS PASSED
~~~

These checks run against temporary fictional records, not real student data.
