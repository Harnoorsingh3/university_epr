import sqlite3
import pytest
from werkzeug.security import generate_password_hash
from app import create_app

@pytest.fixture
def app(tmp_path):
    app=create_app({"TESTING": True, "DATABASE": str(tmp_path/"test.sqlite3"), "SECRET_KEY": "testing-only-secret"})
    with app.app_context():
        con=sqlite3.connect(app.config["DATABASE"])
        con.executescript(open("schema.sql",encoding="utf8").read())
        con.execute("INSERT INTO users(username,password_hash,role) VALUES (?,?,?)",("admin",generate_password_hash("secure-password-123"),"admin"))
        con.execute("INSERT INTO students(roll_no,name,email) VALUES (?,?,?)",("S001","Student One","one@example.test"))
        con.execute("INSERT INTO students(roll_no,name,email) VALUES (?,?,?)",("S002","Student Two","two@example.test"))
        con.execute("INSERT INTO users(username,password_hash,role,student_id) VALUES (?,?,?,?)",("student",generate_password_hash("secure-password-123"),"student",1))
        con.execute("INSERT INTO fees(student_id,description,amount,due_date) VALUES (?,?,?,?)",(1,"Tuition",1000,"2027-01-01"))
        con.execute("INSERT INTO fees(student_id,description,amount,due_date) VALUES (?,?,?,?)",(2,"Private fee",2000,"2027-01-01"))
        con.commit()
        con.close()
    return app

def login(client,username):
    response=client.get("/login")
    with client.session_transaction() as sess:
        csrf=sess["csrf"]
    return client.post("/login",data={"username":username,"password":"secure-password-123","csrf_token":csrf},follow_redirects=True)

def test_login_and_dashboard(app):
    c=app.test_client()
    assert login(c,"admin").status_code==200
    assert b"Dashboard" in c.get("/dashboard").data

def test_student_fee_isolation(app):
    c=app.test_client()
    login(c,"student")
    response=c.get("/module/fees")
    assert b"Tuition" in response.data
    assert b"Private fee" not in response.data

def test_student_forbidden_admin_accounts(app):
    c=app.test_client()
    login(c,"student")
    assert c.get("/accounts").status_code==403

def test_csrf_rejects_unprotected_write(app):
    c=app.test_client()
    login(c,"admin")
    assert c.post("/module/departments/add",data={"code":"CSE","name":"Computer Science"}).status_code==400

def test_admin_can_create_department(app):
    c=app.test_client()
    login(c,"admin")
    with c.session_transaction() as sess: csrf=sess["csrf"]
    response=c.post("/module/departments/add",data={"csrf_token":csrf,"code":"CSE","name":"Computer Science"},follow_redirects=True)
    assert response.status_code==200
    assert b"Computer Science" in response.data
