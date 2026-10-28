import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db(conn):
    cursor = conn.cursor()
    
    # Check users columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    if columns:
        if 'email' not in columns:
            try: cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            except Exception: pass
        if 'department' not in columns:
            try: cursor.execute("ALTER TABLE users ADD COLUMN department TEXT")
            except Exception: pass
        if 'student_id' not in columns:
            try: cursor.execute("ALTER TABLE users ADD COLUMN student_id INTEGER")
            except Exception: pass

    # Check students columns
    cursor.execute("PRAGMA table_info(students)")
    s_columns = [row['name'] for row in cursor.fetchall()]
    if s_columns:
        if 'email' not in s_columns:
            try: cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
            except Exception: pass
        if 'assigned_faculty_id' not in s_columns:
            try: cursor.execute("ALTER TABLE students ADD COLUMN assigned_faculty_id INTEGER")
            except Exception: pass

    # Check interventions columns
    cursor.execute("PRAGMA table_info(interventions)")
    i_columns = [row['name'] for row in cursor.fetchall()]
    if i_columns:
        if 'faculty_id' not in i_columns:
            try: cursor.execute("ALTER TABLE interventions ADD COLUMN faculty_id INTEGER")
            except Exception: pass
            
    conn.commit()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table (Admin, Faculty, Student)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            department TEXT,
            student_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')

    # Students Roster Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            assigned_faculty_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_faculty_id) REFERENCES users (id)
        )
    ''')

    # Prediction Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            user_id INTEGER,
            study_hours REAL NOT NULL,
            attendance REAL NOT NULL,
            past_grade REAL NOT NULL,
            assignment_completion REAL NOT NULL,
            sleep_hours REAL NOT NULL,
            extracurricular_score REAL NOT NULL,
            predicted_score REAL NOT NULL,
            performance_category TEXT NOT NULL,
            shap_json TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Interventions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interventions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            faculty_id INTEGER,
            prediction_id INTEGER,
            target_feature TEXT NOT NULL,
            baseline_value REAL NOT NULL,
            target_value REAL NOT NULL,
            status TEXT DEFAULT 'Planned',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (faculty_id) REFERENCES users (id),
            FOREIGN KEY (prediction_id) REFERENCES prediction_logs (id)
        )
    ''')

    # Run column migration checks
    migrate_db(conn)

    # Seed Default Accounts if admin is missing
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash("admin123")
        faculty_hash = generate_password_hash("faculty123")
        student_hash = generate_password_hash("student123")

        # 1. Admin Account
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("admin", "admin@college.edu", admin_hash, "Dr. Sarah Jenkins (Dean & College Admin)", "admin", "Academic Affairs"))

        # 2. Faculty Accounts
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("prof_smith", "smith@college.edu", faculty_hash, "Prof. Alan Smith", "faculty", "Computer Science"))
        faculty1_id = cursor.lastrowid

        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("prof_davis", "davis@college.edu", faculty_hash, "Prof. Clara Davis", "faculty", "Data Science"))
        faculty2_id = cursor.lastrowid

        # 3. Seed Students Roster
        sample_students = [
            ("STU-1001", "Alex Morgan", "alex@student.edu", "Computer Science", "Year 3", faculty1_id),
            ("STU-1002", "Bella Chen", "bella@student.edu", "Data Science", "Year 2", faculty2_id),
            ("STU-1003", "Carlos Rodriguez", "carlos@student.edu", "Computer Science", "Year 3", faculty1_id),
            ("STU-1004", "Diana Prince", "diana@student.edu", "Information Systems", "Year 1", faculty1_id),
            ("STU-1005", "Ethan Hunt", "ethan@student.edu", "Computer Science", "Year 4", faculty2_id)
        ]
        
        for code, name, email, dept, grade, fac_id in sample_students:
            cursor.execute('''
                INSERT OR IGNORE INTO students (student_code, name, email, department, grade_level, assigned_faculty_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, name, email, dept, grade, fac_id))
            stu_id = cursor.lastrowid

            if code == "STU-1001":
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, department, student_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ("stu_alex", email, student_hash, name, "student", dept, stu_id))
            elif code == "STU-1002":
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role, department, student_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ("stu_bella", email, student_hash, name, "student", dept, stu_id))

    conn.commit()
    conn.close()

def reset_and_seed_db():
    db_path = Config.DATABASE
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Removed old database file to apply clean multi-role schema.")
        except Exception as e:
            print(f"Could not remove old DB file: {e}")
    init_db()

if __name__ == '__main__':
    reset_and_seed_db()
    print("Database reset & migration completed successfully.")
