"""University ERP learning project: Flask + SQLite."""
import os
import sqlite3
import secrets
from pathlib import Path
from functools import wraps
import click
from flask import Flask, g, session, request, redirect, url_for, flash, abort, render_template_string
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
FIELDS = {
 "departments":["code","name"],
 "students":["roll_no","name","email","department_id","semester"],
 "faculty":["employee_no","name","email","department_id"],
 "courses":["code","title","credits","department_id","faculty_id","semester"],
 "enrollments":["student_id","course_id","status"],
 "fees":["student_id","description","amount","due_date","status"],
 "announcements":["title","body"],
 "timetable":["course_id","day","starts_at","ends_at","room"],
 "library_books":["isbn","title","author","copies"],
 "library_loans":["book_id","student_id","issued_on","due_on","returned_on"],
 "hostel_rooms":["block","room_number","capacity"],
 "hostel_allocations":["room_id","student_id","allocated_on"],
 "tickets":["student_id","subject","description","status"]
}
NUMBERS={"department_id","faculty_id","student_id","course_id","book_id","room_id","semester","credits","copies","capacity","enrollment_id"}
LAYOUT="""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} | UniERP</title><link rel="stylesheet" href="{{ url_for('static',filename='style.css') }}"></head><body><header><a class="brand" href="{{ url_for('dashboard') }}">🎓 UniERP</a>{% if g.user %}<nav><a href="{{ url_for('dashboard') }}">Dashboard</a>{% if g.user['role']=='admin' %}<a href="{{ url_for('accounts') }}">Accounts</a>{% endif %}<a href="{{ url_for('password') }}">Password</a><form method="post" action="{{ url_for('logout') }}"><input type="hidden" name="csrf_token" value="{{ csrf }}"><button class="link">Sign out</button></form></nav>{% endif %}</header><main><div class="head"><h1>{{ title }}</h1>{% if g.user %}<span class="pill">{{ g.user['username'] }} · {{ g.user['role'] }}</span>{% endif %}</div>{% with messages=get_flashed_messages(with_categories=true) %}{% for kind,message in messages %}<div class="alert {{ kind }}">{{ message }}</div>{% endfor %}{% endwith %}{{ content|safe }}</main><footer>UniERP · starter project · use fictional data only</footer></body></html>"""

def create_app(test_config=None):
 app=Flask(__name__,instance_relative_config=True)
 app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
                   DATABASE=str(Path(app.instance_path)/"university.sqlite3"),
                   SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",
                   SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE")=="1")
 if test_config: app.config.update(test_config)
 os.makedirs(app.instance_path,exist_ok=True)

 def db():
  if "db" not in g:
   g.db=sqlite3.connect(app.config["DATABASE"])
   g.db.row_factory=sqlite3.Row
   g.db.execute("PRAGMA foreign_keys=ON")
  return g.db

 @app.teardown_appcontext
 def close(error):
  conn=g.pop("db",None)
  if conn: conn.close()

 def init_db():
  db().executescript((BASE/"schema.sql").read_text(encoding="utf8"))
  db().commit()

 @app.cli.command("init-db")
 def init_db_cli():
  init_db()
  click.echo("Database ready.")

 @app.cli.command("init-admin")
 @click.option("--username",prompt=True)
 @click.password_option()
 def init_admin(username,password):
  init_db()
  if len(password)<12: raise click.ClickException("Password must contain at least 12 characters.")
  if db().execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]:
   raise click.ClickException("Admin already exists. Add accounts in the dashboard.")
  try:
   db().execute("INSERT INTO users(username,password_hash,role) VALUES (?,?,?)",
                (username.strip(),generate_password_hash(password),"admin"))
   db().commit()
  except sqlite3.IntegrityError as exc:
   raise click.ClickException("Username already in use.") from exc
  click.echo("Admin created.")

 @app.before_request
 def before():
  g.user=None
  if session.get("uid"):
   g.user=db().execute("SELECT * FROM users WHERE id=? AND active=1",(session["uid"],)).fetchone()
   if not g.user: session.clear()
  if "csrf" not in session: session["csrf"]=secrets.token_urlsafe(32)
  if request.method=="POST" and not secrets.compare_digest(session["csrf"],request.form.get("csrf_token","")):
   abort(400,"Invalid CSRF token")

 def page(title,template,**kw):
  inner=render_template_string(template,csrf=session["csrf"],**kw)
  return render_template_string(LAYOUT,title=title,content=inner,csrf=session["csrf"])

 def login_required(fn):
  @wraps(fn)
  def decorated(*args,**kwargs):
   if not g.user:return redirect(url_for("login"))
   return fn(*args,**kwargs)
  return decorated

 def role_required(*roles):
  def outer(fn):
   @wraps(fn)
   @login_required
   def decorated(*args,**kwargs):
    if g.user["role"] not in roles:abort(403)
    return fn(*args,**kwargs)
   return decorated
  return outer

 def audit(action,table,pk):
  db().execute("INSERT INTO audit_logs(user_id,action,table_name,record_id) VALUES(?,?,?,?)",
               (g.user["id"],action,table,pk))

 @app.get("/")
 def index():
  return redirect(url_for("dashboard") if g.user else url_for("login"))

 @app.route("/login",methods=["GET","POST"])
 def login():
  if g.user:return redirect(url_for("dashboard"))
  if request.method=="POST":
   user=db().execute("SELECT * FROM users WHERE username=? AND active=1",
                     (request.form.get("username","").strip(),)).fetchone()
   if user and check_password_hash(user["password_hash"],request.form.get("password","")):
    session.clear()
    session["uid"]=user["id"]
    session["csrf"]=secrets.token_urlsafe(32)
    return redirect(url_for("dashboard"))
   flash("Invalid username or password.","error")
  return page("Sign in","""<div class="card narrow"><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf }}"><label>Username<input name="username" required autocomplete="username"></label><label>Password<input name="password" type="password" required autocomplete="current-password"></label><button>Sign in</button></form><p class="muted">First time? Run the setup commands in README.md to create an administrator.</p></div>""")

 @app.post("/logout")
 @login_required
 def logout():
  session.clear()
  return redirect(url_for("login"))

 @app.route("/password",methods=["GET","POST"])
 @login_required
 def password():
  if request.method=="POST":
   current=request.form.get("current","")
   new=request.form.get("new","")
   if not check_password_hash(g.user["password_hash"],current):
    flash("Wrong current password.","error")
   elif len(new)<12:
    flash("Use at least 12 characters.","error")
   else:
    db().execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(new),g.user["id"]))
    db().commit()
    flash("Password changed.","success")
    return redirect(url_for("dashboard"))
  return page("Change password","""<div class="card narrow"><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf }}"><label>Current password<input name="current" type="password" required></label><label>New password (12+ characters)<input name="new" type="password" minlength="12" required></label><button>Update</button></form></div>""")

 def scope(table):
  role=g.user["role"]
  if role=="admin":return "",[]
  if role=="student":
   sid=g.user["student_id"] or -1
   clauses={
    "students":("id=?",[sid]),
    "courses":("id IN (SELECT course_id FROM enrollments WHERE student_id=?)",[sid]),
    "attendance":("enrollment_id IN (SELECT id FROM enrollments WHERE student_id=?)",[sid]),
    "grades":("enrollment_id IN (SELECT id FROM enrollments WHERE student_id=?)",[sid]),
    "fees":("student_id=?",[sid]),
    "timetable":("course_id IN (SELECT course_id FROM enrollments WHERE student_id=?)",[sid]),
    "library_loans":("student_id=?",[sid]),
    "hostel_allocations":("student_id=?",[sid]),
    "tickets":("student_id=?",[sid]),
    "announcements":("",[])}
  else:
   fid=g.user["faculty_id"] or -1
   clauses={
    "courses":("faculty_id=?",[fid]),
    "enrollments":("course_id IN (SELECT id FROM courses WHERE faculty_id=?)",[fid]),
    "attendance":("enrollment_id IN (SELECT e.id FROM enrollments e JOIN courses c ON e.course_id=c.id WHERE c.faculty_id=?)",[fid]),
    "grades":("enrollment_id IN (SELECT e.id FROM enrollments e JOIN courses c ON e.course_id=c.id WHERE c.faculty_id=?)",[fid]),
    "timetable":("course_id IN (SELECT id FROM courses WHERE faculty_id=?)",[fid]),
    "announcements":("",[])}
  if table not in clauses:abort(403)
  return clauses[table]

 @app.get("/dashboard")
 @login_required
 def dashboard():
  if g.user["role"]=="admin":mods=list(FIELDS)+["attendance","grades"]
  elif g.user["role"]=="faculty":mods=["courses","enrollments","attendance","grades","timetable","announcements"]
  else:mods=["students","courses","attendance","grades","fees","timetable","announcements","library_loans","hostel_allocations","tickets"]
  counts={}
  if g.user["role"]=="admin":
   for table in ("students","faculty","courses","enrollments","fees","tickets"):
    counts[table]=db().execute("SELECT COUNT(*) FROM "+table).fetchone()[0]
  return page("Dashboard","""{% if counts %}<div class="stats">{% for name,n in counts.items() %}<div class="card stat"><strong>{{ n }}</strong><small>{{ name|title }}</small></div>{% endfor %}</div>{% endif %}<div class="grid">{% for key in mods %}<a class="card module" href="{{ url_for('module',name=key) }}">{{ key.replace('_',' ')|title }} <b>→</b></a>{% endfor %}</div>""",mods=mods,counts=counts)

 @app.get("/module/<name>")
 @login_required
 def module(name):
  if name not in FIELDS and name not in ("attendance","grades"):abort(404)
  condition,params=scope(name)
  query="SELECT * FROM "+name+(" WHERE "+condition if condition else "")+" ORDER BY id DESC LIMIT 300"
  rows=[dict(x) for x in db().execute(query,params)]
  cols=list(rows[0]) if rows else ["id"]+FIELDS.get(name,["enrollment_id","class_date","status"] if name=="attendance" else ["enrollment_id","assessment","score","max_score"])
  can_add=g.user["role"]=="admin" and name in FIELDS or (g.user["role"]=="student" and name=="tickets")
  can_record=name in ("attendance","grades") and g.user["role"] in ("admin","faculty")
  return page(name.replace("_"," ").title(),"""<div class="actions"><a class="button ghost" href="{{ url_for('dashboard') }}">← Back</a>{% if can_add %}<a class="button" href="{{ url_for('add_item',name=name) }}">+ Add record</a>{% endif %}{% if can_record %}<a class="button" href="{{ url_for('academic',name=name) }}">Record {{ name }}</a>{% endif %}</div><div class="scroll"><table><thead><tr>{% for col in cols %}<th>{{ col.replace('_',' ')|title }}</th>{% endfor %}</tr></thead><tbody>{% for row in rows %}<tr>{% for col in cols %}<td>{{ row[col] if row[col] is not none else '—' }}</td>{% endfor %}</tr>{% else %}<tr><td colspan="{{ cols|length }}">No records found.</td></tr>{% endfor %}</tbody></table></div><p class="muted">Up to 300 entries; student and faculty records are scoped to their account.</p>""",name=name,rows=rows,cols=cols,can_add=can_add,can_record=can_record)

 @app.route("/module/<name>/add",methods=["GET","POST"])
 @login_required
 def add_item(name):
  if name not in FIELDS:abort(404)
  is_ticket=name=="tickets" and g.user["role"]=="student"
  if g.user["role"]!="admin" and not is_ticket:abort(403)
  fields=["subject","description"] if is_ticket else FIELDS[name]
  if request.method=="POST":
   values=[]
   for field in fields:
    val=request.form.get(field,"").strip()
    if field in NUMBERS and val:
     try:val=int(val)
     except ValueError:
      flash("Invalid integer: "+field,"error")
      return redirect(request.url)
    values.append(val if val!="" else None)
   ins_fields=list(fields)
   if is_ticket:
    if not g.user["student_id"]:abort(403)
    ins_fields.insert(0,"student_id")
    values.insert(0,g.user["student_id"])
   try:
    cur=db().execute("INSERT INTO "+name+"("+",".join(ins_fields)+") VALUES("+",".join("?" for _ in ins_fields)+")",values)
    audit("create",name,cur.lastrowid)
    db().commit()
    flash("Record added.","success")
    return redirect(url_for("module",name=name))
   except sqlite3.IntegrityError:
    db().rollback()
    flash("Invalid or duplicate data. Check referenced record IDs and required fields.","error")
  return page("Add "+name.replace("_"," ").title(),"""<div class="card narrow"><p class="muted">Enter valid IDs from related modules for foreign key fields. Dates use YYYY-MM-DD; times use HH:MM.</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf }}">{% for field in fields %}<label>{{ field.replace('_',' ')|title }}<input name="{{ field }}" {% if field not in ['department_id','faculty_id','returned_on'] %}required{% endif %} placeholder="{{ 'YYYY-MM-DD' if 'date' in field or field.endswith('_on') else 'HH:MM' if field in ['starts_at','ends_at'] else field }}"></label>{% endfor %}<button>Add record</button></form></div>""",fields=fields)

 @app.route("/academic/<name>",methods=["GET","POST"])
 @role_required("admin","faculty")
 def academic(name):
  if name not in ("attendance","grades"):abort(404)
  fields=["enrollment_id","class_date","status"] if name=="attendance" else ["enrollment_id","assessment","score","max_score"]
  if request.method=="POST":
   try: eid=int(request.form["enrollment_id"])
   except (KeyError,ValueError):abort(400)
   if g.user["role"]=="faculty":
    valid=db().execute("SELECT 1 FROM enrollments e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND c.faculty_id=?",(eid,g.user["faculty_id"])).fetchone()
    if not valid:abort(403)
   else:
    if not db().execute("SELECT 1 FROM enrollments WHERE id=?",(eid,)).fetchone():abort(400)
   vals=[request.form.get(f,"").strip() for f in fields]
   if name=="attendance" and vals[2] not in ("present","absent","late"):abort(400)
   try:
    if name=="grades":
     vals[2],vals[3]=float(vals[2]),float(vals[3])
    db().execute("INSERT INTO "+name+"("+",".join(fields)+") VALUES("+",".join("?" for _ in fields)+") ON CONFLICT(enrollment_id,"+("class_date" if name=="attendance" else "assessment")+") DO UPDATE SET "+("status=excluded.status" if name=="attendance" else "score=excluded.score,max_score=excluded.max_score"),vals)
    audit("upsert",name,eid)
    db().commit()
    flash("Saved.","success")
    return redirect(url_for("module",name=name))
   except (sqlite3.IntegrityError,ValueError):
    db().rollback()
    flash("Invalid attendance/grade values.","error")
  return page("Record "+name,"""<div class="card narrow"><p class="muted">Use an enrollment ID from the enrollments module. Faculty can record only for their assigned courses.</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf }}">{% for field in fields %}<label>{{ field.replace('_',' ')|title }}<input name="{{ field }}" placeholder="{{ 'YYYY-MM-DD' if field=='class_date' else field }}" required></label>{% endfor %}<button>Save</button></form></div>""",fields=fields)

 @app.route("/accounts",methods=["GET","POST"])
 @role_required("admin")
 def accounts():
  if request.method=="POST":
   username=request.form.get("username","").strip()
   pw=request.form.get("password","")
   role=request.form.get("role","")
   if len(pw)<12 or role not in ("admin","faculty","student") or not username:
    flash("Provide a username, role and password of at least 12 characters.","error")
   else:
    try:
     sid=int(request.form.get("student_id") or 0) or None
     fid=int(request.form.get("faculty_id") or 0) or None
     if (role=="student" and sid is None) or (role=="faculty" and fid is None):
      flash("Student/faculty accounts require their matching record ID.","error")
     else:
      cur=db().execute("INSERT INTO users(username,password_hash,role,student_id,faculty_id) VALUES(?,?,?,?,?)",
           (username,generate_password_hash(pw),role,sid if role=="student" else None,fid if role=="faculty" else None))
      audit("create","users",cur.lastrowid)
      db().commit()
      flash("Account created.","success")
      return redirect(url_for("accounts"))
    except (ValueError,sqlite3.IntegrityError):
     db().rollback()
     flash("Invalid ID or duplicate username/account mapping.","error")
  users=[dict(r) for r in db().execute("SELECT id,username,role,student_id,faculty_id,active FROM users ORDER BY id")]
  return page("User accounts","""<div class="card"><h2>Create login</h2><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf }}"><label>Username<input name="username" required></label><label>Password (12+ characters)<input type="password" minlength="12" name="password" required></label><label>Role<select name="role"><option>student</option><option>faculty</option><option>admin</option></select></label><label>Student record ID (for student only)<input type="number" name="student_id"></label><label>Faculty record ID (for faculty only)<input type="number" name="faculty_id"></label><button>Create account</button></form></div><h2>Accounts</h2><div class="scroll"><table><tr><th>ID</th><th>Username</th><th>Role</th><th>Student ID</th><th>Faculty ID</th><th>Active</th></tr>{% for u in users %}<tr><td>{{u.id}}</td><td>{{u.username}}</td><td>{{u.role}}</td><td>{{u.student_id or '—'}}</td><td>{{u.faculty_id or '—'}}</td><td>{{u.active}}</td></tr>{% endfor %}</table></div>""",users=users)

 @app.errorhandler(403)
 def forbidden(error):
  return page("Access denied","<p>You do not have access to this resource.</p>"),403

 @app.errorhandler(404)
 def missing(error):
  return page("Not found","<p>This page does not exist.</p>"),404

 return app

if __name__=="__main__":
 create_app().run(debug=False)
