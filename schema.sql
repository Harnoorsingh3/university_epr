PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','faculty','student')),
 student_id INTEGER UNIQUE,
 faculty_id INTEGER UNIQUE,
 active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS departments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS students (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 roll_no TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 email TEXT NOT NULL,
 department_id INTEGER REFERENCES departments(id),
 semester INTEGER NOT NULL DEFAULT 1 CHECK(semester BETWEEN 1 AND 12)
);
CREATE TABLE IF NOT EXISTS faculty (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 employee_no TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 email TEXT NOT NULL,
 department_id INTEGER REFERENCES departments(id)
);
CREATE TABLE IF NOT EXISTS courses (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 title TEXT NOT NULL,
 credits INTEGER NOT NULL DEFAULT 3 CHECK(credits BETWEEN 1 AND 12),
 department_id INTEGER REFERENCES departments(id),
 faculty_id INTEGER REFERENCES faculty(id),
 semester INTEGER NOT NULL DEFAULT 1 CHECK(semester BETWEEN 1 AND 12)
);
CREATE TABLE IF NOT EXISTS enrollments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
 course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','dropped')),
 UNIQUE(student_id,course_id)
);
CREATE TABLE IF NOT EXISTS attendance (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
 class_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('present','absent','late')),
 UNIQUE(enrollment_id,class_date)
);
CREATE TABLE IF NOT EXISTS grades (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
 assessment TEXT NOT NULL,
 score REAL NOT NULL CHECK(score >= 0),
 max_score REAL NOT NULL CHECK(max_score > 0),
 UNIQUE(enrollment_id,assessment),
 CHECK(score <= max_score)
);
CREATE TABLE IF NOT EXISTS fees (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES students(id),
 description TEXT NOT NULL,
 amount REAL NOT NULL CHECK(amount >= 0),
 due_date TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','paid','overdue'))
);
CREATE TABLE IF NOT EXISTS announcements (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 body TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS timetable (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 course_id INTEGER NOT NULL REFERENCES courses(id),
 day TEXT NOT NULL CHECK(day IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
 starts_at TEXT NOT NULL,
 ends_at TEXT NOT NULL,
 room TEXT NOT NULL,
 CHECK(starts_at < ends_at)
);
CREATE TABLE IF NOT EXISTS library_books (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 isbn TEXT NOT NULL UNIQUE,
 title TEXT NOT NULL,
 author TEXT NOT NULL,
 copies INTEGER NOT NULL DEFAULT 1 CHECK(copies >= 0)
);
CREATE TABLE IF NOT EXISTS library_loans (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 book_id INTEGER NOT NULL REFERENCES library_books(id),
 student_id INTEGER NOT NULL REFERENCES students(id),
 issued_on TEXT NOT NULL,
 due_on TEXT NOT NULL,
 returned_on TEXT
);
CREATE TABLE IF NOT EXISTS hostel_rooms (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 block TEXT NOT NULL,
 room_number TEXT NOT NULL,
 capacity INTEGER NOT NULL CHECK(capacity > 0),
 UNIQUE(block,room_number)
);
CREATE TABLE IF NOT EXISTS hostel_allocations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 room_id INTEGER NOT NULL REFERENCES hostel_rooms(id),
 student_id INTEGER NOT NULL UNIQUE REFERENCES students(id),
 allocated_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES students(id),
 subject TEXT NOT NULL,
 description TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','resolved')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER REFERENCES users(id),
 action TEXT NOT NULL,
 table_name TEXT NOT NULL,
 record_id INTEGER,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_courses_faculty ON courses(faculty_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_enrollment ON attendance(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_fees_student ON fees(student_id);
CREATE INDEX IF NOT EXISTS idx_tickets_student ON tickets(student_id);
