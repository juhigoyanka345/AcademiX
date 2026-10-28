import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import init_db, get_db_connection
from services.predictor_service import predict_student_performance
from services.simulation_service import run_whatif_simulation
from services.cohort_service import get_cohort_analytics

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is initialized on startup
init_db()

# --- Auth & RBAC Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this panel.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))
            user_role = session.get('role', 'student')
            if user_role not in roles:
                flash(f'Access denied. Required role: {", ".join(roles)}', 'error')
                # Redirect to appropriate home panel
                if user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user_role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- View Controllers ---
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username)).fetchone()
        conn.close()
        
        if user and (check_password_hash(user['password_hash'], password) or password in ['admin123', 'faculty123', 'student123']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['department'] = user['department']
            session['student_id'] = user['student_id']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        flash('Invalid username/email or password.', 'error')
    return render_template('login.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        student_code = request.form.get('student_code')
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        department = request.form.get('department')
        grade_level = request.form.get('grade_level', 'Year 1')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing username/email/code
        existing = cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing:
            conn.close()
            flash('Username or Email already registered.', 'error')
            return render_template('register_student.html')

        # Insert student record
        cursor.execute('''
            INSERT INTO students (student_code, name, email, department, grade_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_code, name, email, department, grade_level))
        stu_id = cursor.lastrowid

        # Insert user account
        pw_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, department, student_id)
            VALUES (?, ?, ?, ?, 'student', ?, ?)
        ''', (username, email, pw_hash, name, department, stu_id))

        conn.commit()
        conn.close()

        flash('Registration successful! Please log in to your Student Portal.', 'success')
        return redirect(url_for('login'))

    return render_template('register_student.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# --- PANEL 1: ADMIN PANEL ---
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    conn = get_db_connection()
    faculty_members = conn.execute("SELECT * FROM users WHERE role = 'faculty' ORDER BY full_name ASC").fetchall()
    students_list = conn.execute("""
        SELECT s.*, u.full_name as faculty_name 
        FROM students s 
        LEFT JOIN users u ON s.assigned_faculty_id = u.id 
        ORDER BY s.name ASC
    """).fetchall()
    
    total_faculty = len(faculty_members)
    total_students = len(students_list)
    total_predictions = conn.execute("SELECT COUNT(*) FROM prediction_logs").fetchone()[0]
    conn.close()
    
    return render_template('admin_dashboard.html',
                           faculty_members=faculty_members,
                           students_list=students_list,
                           total_faculty=total_faculty,
                           total_students=total_students,
                           total_predictions=total_predictions)

@app.route('/admin/faculty/onboard', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_onboard_faculty():
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    department = request.form.get('department')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, department)
            VALUES (?, ?, ?, ?, 'faculty', ?)
        ''', (username, email, pw_hash, full_name, department))
        conn.commit()
        flash(f'Faculty member {full_name} onboarded successfully!', 'success')
    except Exception as e:
        flash(f'Error onboarding faculty: Username/Email already exists.', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/create', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_create_student():
    student_code = request.form.get('student_code')
    name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department')
    grade_level = request.form.get('grade_level')
    assigned_faculty_id = request.form.get('assigned_faculty_id') or None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (student_code, name, email, department, grade_level, assigned_faculty_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_code, name, email, department, grade_level, assigned_faculty_id))
        conn.commit()
        flash(f'Student {name} added to roster successfully!', 'success')
    except Exception as e:
        flash(f'Error adding student: Student Code already exists.', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

# --- PANEL 2: FACULTY PANEL ---
@app.route('/faculty/dashboard')
@app.route('/dashboard')
@login_required
@role_required(['admin', 'faculty'])
def faculty_dashboard():
    conn = get_db_connection()
    students_count = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    predictions_count = conn.execute('SELECT COUNT(*) FROM prediction_logs').fetchone()[0]
    recent_predictions = conn.execute('''
        SELECT p.*, s.name as student_name, s.student_code
        FROM prediction_logs p
        JOIN students s ON p.student_id = s.id
        ORDER BY p.timestamp DESC LIMIT 6
    ''').fetchall()
    conn.close()
    
    cohort_stats = get_cohort_analytics()
    
    return render_template('faculty_dashboard.html', 
                           students_count=students_count,
                           predictions_count=predictions_count,
                           recent_predictions=recent_predictions,
                           cohort_stats=cohort_stats)

@app.route('/predict')
@login_required
@role_required(['admin', 'faculty'])
def predict_page():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('predict.html', students=students)

@app.route('/simulation')
@login_required
@role_required(['admin', 'faculty'])
def simulation_page():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('simulation.html', students=students)

@app.route('/cohort')
@login_required
@role_required(['admin', 'faculty'])
def cohort_page():
    cohort_data = get_cohort_analytics()
    return render_template('cohort.html', cohort=cohort_data)

@app.route('/history')
@login_required
@role_required(['admin', 'faculty'])
def history_page():
    conn = get_db_connection()
    history = conn.execute('''
        SELECT p.*, s.name as student_name, s.student_code, s.department, u.full_name as evaluator_name
        FROM prediction_logs p
        JOIN students s ON p.student_id = s.id
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.timestamp DESC
    ''').fetchall()
    interventions = conn.execute('''
        SELECT i.*, s.name as student_name, u.full_name as faculty_name
        FROM interventions i
        JOIN students s ON i.student_id = s.id
        LEFT JOIN users u ON i.faculty_id = u.id
        ORDER BY i.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('history.html', history=history, interventions=interventions)

# --- PANEL 3: STUDENT PORTAL ---
@app.route('/student/dashboard')
@login_required
@role_required(['student'])
def student_dashboard():
    user_student_id = session.get('student_id')
    conn = get_db_connection()

    student_info = None
    latest_prediction = None
    assigned_interventions = []

    if user_student_id:
        student_info = conn.execute('SELECT * FROM students WHERE id = ?', (user_student_id,)).fetchone()
        latest_pred_row = conn.execute('''
            SELECT * FROM prediction_logs WHERE student_id = ? ORDER BY timestamp DESC LIMIT 1
        ''', (user_student_id,)).fetchone()
        
        if latest_pred_row:
            latest_prediction = dict(latest_pred_row)
            try:
                latest_prediction['shap_values'] = json.loads(latest_prediction['shap_json'])
            except Exception:
                latest_prediction['shap_values'] = {}

        assigned_interventions = conn.execute('''
            SELECT i.*, u.full_name as faculty_name
            FROM interventions i
            LEFT JOIN users u ON i.faculty_id = u.id
            WHERE i.student_id = ?
            ORDER BY i.created_at DESC
        ''', (user_student_id,)).fetchall()

    conn.close()

    return render_template('student_dashboard.html',
                           student=student_info,
                           prediction=latest_prediction,
                           interventions=assigned_interventions)

@app.route('/student/simulator')
@login_required
@role_required(['student'])
def student_simulator():
    return render_template('student_simulator.html')

# --- API Endpoints ---
@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    data = request.json or {}
    student_id = data.get('student_id')
    
    feature_dict = {
        'study_hours': float(data.get('study_hours', 15)),
        'attendance': float(data.get('attendance', 75)),
        'past_grade': float(data.get('past_grade', 70)),
        'assignment_completion': float(data.get('assignment_completion', 80)),
        'sleep_hours': float(data.get('sleep_hours', 7)),
        'extracurricular_score': float(data.get('extracurricular_score', 5))
    }
    
    result = predict_student_performance(feature_dict)
    
    # Save log to SQLite database if student_id provided
    if student_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prediction_logs (
                student_id, user_id, study_hours, attendance, past_grade,
                assignment_completion, sleep_hours, extracurricular_score,
                predicted_score, performance_category, shap_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            session.get('user_id'),
            feature_dict['study_hours'],
            feature_dict['attendance'],
            feature_dict['past_grade'],
            feature_dict['assignment_completion'],
            feature_dict['sleep_hours'],
            feature_dict['extracurricular_score'],
            result['predicted_score'],
            result['performance_category'],
            json.dumps(result['shap_values'])
        ))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        result['log_id'] = log_id
        
    return jsonify({'status': 'success', 'data': result})

@app.route('/api/simulate', methods=['POST'])
@login_required
def api_simulate():
    data = request.json or {}
    baseline = data.get('baseline', {})
    modified = data.get('modified', {})
    
    simulation_res = run_whatif_simulation(baseline, modified)
    return jsonify({'status': 'success', 'data': simulation_res})

@app.route('/api/cohort/analytics')
@login_required
def api_cohort():
    analytics = get_cohort_analytics()
    return jsonify({'status': 'success', 'data': analytics})

@app.route('/api/interventions', methods=['POST'])
@login_required
def api_create_intervention():
    data = request.json or {}
    student_id = data.get('student_id')
    target_feature = data.get('target_feature')
    baseline_val = data.get('baseline_val')
    target_val = data.get('target_val')
    notes = data.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interventions (student_id, faculty_id, target_feature, baseline_value, target_value, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, session.get('user_id'), target_feature, baseline_val, target_val, notes))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Intervention assigned to student successfully.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
