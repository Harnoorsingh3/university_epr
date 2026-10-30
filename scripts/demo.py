"""Safe demo/smoke output using fictional sample records and Flask's test client."""
import os
import sys
import tempfile
from pathlib import Path
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app

with tempfile.TemporaryDirectory() as tmp:
    app = create_app({"TESTING": True, "DATABASE": str(Path(tmp) / "demo.sqlite3"), "SECRET_KEY": "demo-run-not-for-production"})
    with app.app_context():
        conn = app.test_client()
        db = app.extensions.get("unused", None)
        import sqlite3
        con = sqlite3.connect(app.config["DATABASE"])
        con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        con.execute("INSERT INTO departments(code,name) VALUES (?,?)", ("CSE", "Computer Science"))
        con.execute("INSERT INTO students(roll_no,name,email,department_id,semester) VALUES (?,?,?,?,?)",
                    ("DEMO001", "Demo Student", "demo-student@example.test", 1, 3))
        con.execute("INSERT INTO faculty(employee_no,name,email,department_id) VALUES (?,?,?,?)",
                    ("FAC001", "Demo Faculty", "faculty@example.test", 1))
        con.execute("INSERT INTO courses(code,title,credits,department_id,faculty_id,semester) VALUES (?,?,?,?,?,?)",
                    ("CSE101", "Programming Fundamentals", 3, 1, 1, 3))
        con.execute("INSERT INTO enrollments(student_id,course_id) VALUES (?,?)", (1,1))
        con.execute("INSERT INTO attendance(enrollment_id,class_date,status) VALUES (?,?,?)",
                    (1,"2026-10-15","present"))
        con.execute("INSERT INTO grades(enrollment_id,assessment,score,max_score) VALUES (?,?,?,?)",
                    (1,"Quiz 1",17,20))
        con.execute("INSERT INTO fees(student_id,description,amount,due_date,status) VALUES (?,?,?,?,?)",
                    (1,"Semester fees (demo)",15000,"2026-12-01","pending"))
        con.execute("INSERT INTO announcements(title,body) VALUES (?,?)",
                    ("Welcome!", "This is demo data, not real university information."))
        con.execute("INSERT INTO users(username,password_hash,role) VALUES (?,?,?)",
                    ("demo_admin",generate_password_hash("demo-only-password-123"),"admin"))
        con.execute("INSERT INTO users(username,password_hash,role,student_id) VALUES (?,?,?,?)",
                    ("demo_student",generate_password_hash("demo-only-password-123"),"student",1))
        con.commit()
        con.close()
    client=app.test_client()
    login=client.get("/login")
    assert login.status_code==200
    with client.session_transaction() as sess:
        token=sess["csrf"]
    res=client.post("/login",data={"username":"demo_admin","password":"demo-only-password-123","csrf_token":token},follow_redirects=True)
    assert res.status_code==200 and b"Dashboard" in res.data
    print("UNIVERSITY ERP — DEMO OUTPUT")
    print("Login page: HTTP 200")
    print("Admin login / dashboard: HTTP 200")
    for module in ("departments","students","faculty","courses","enrollments","attendance","grades","fees","announcements","timetable","library_books","hostel_rooms","tickets"):
        response=client.get("/module/"+module)
        assert response.status_code==200,(module,response.status_code)
        print(f"{module}: HTTP {response.status_code}")
    with client.session_transaction() as sess:
        token=sess["csrf"]
    response=client.post("/logout",data={"csrf_token":token},follow_redirects=True)
    assert response.status_code==200
    with client.session_transaction() as sess:
        token=sess["csrf"]
    response=client.post("/login",data={"username":"demo_student","password":"demo-only-password-123","csrf_token":token},follow_redirects=True)
    assert response.status_code==200
    print("Student login / dashboard: HTTP 200")
    response=client.get("/module/fees")
    assert b"Semester fees (demo)" in response.data
    print("Student sees own fee record: PASS")
    response=client.get("/accounts")
    assert response.status_code==403
    print("Student blocked from admin accounts: HTTP 403")
    print("ALL DEMO CHECKS PASSED")
