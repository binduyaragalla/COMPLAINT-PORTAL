from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os

app = Flask(__name__)
app.secret_key = "super_secure_secret_key_change_me" 

UPLOAD_FOLDER = "uploads"
USERS_FILE = "users.csv"
ADMINS_FILE = "admins.csv"
COMPLAINTS_FILE = "complaints.csv"

# --- 1. SETUP FILES & FOLDERS ---
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Email", "PasswordHash"])

if not os.path.exists(COMPLAINTS_FILE):
    with open(COMPLAINTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "StudentID", "Email", "Phone", "Dept", "Category", "Complaint", "FileName"])

# Create an Admin file with a default admin account for testing
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Email", "PasswordHash"])
        # Default Admin: admin@university.edu | Password: admin123
        writer.writerow(["Super Admin", "admin@university.edu", generate_password_hash("admin123")])


# --- 2. HTML TEMPLATES (STORED AS STRINGS) ---

STUDENT_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Student Login</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:#f8f9fc; display:flex; justify-content:center; align-items:center; height:100vh; }
        .card { background:white; padding:40px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.08); width:100%; max-width:400px; text-align:center; border-top: 5px solid #4e73df; }
        h2 { margin-bottom:20px; color:#4e73df; }
        .form-group { margin-bottom:18px; text-align:left; }
        label { font-weight:600; display:block; margin-bottom:6px; color:#333; }
        input { width:100%; padding:10px; border-radius:6px; border:1px solid #ddd; }
        button { width:100%; padding:12px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; background:#4e73df; color:white; margin-top:10px; }
        .links { margin-top:15px; font-size:14px; }
        .links a { color:#4e73df; text-decoration:none; font-weight:bold; }
        .flash { padding:10px; border-radius:5px; margin-bottom:15px; font-size:14px; }
        .flash.error { background:#f8d7da; color:#721c24; }
        .flash.success { background:#d4edda; color:#155724; }
        .switch-role { margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; font-size: 13px; }
        .switch-role a { color: #e74c3c; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Student Login</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form action="/login" method="POST">
            <div class="form-group">
                <label>Student Email</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Log In</button>
        </form>
        <div class="links">
            <p>New student? <a href="/register">Register here</a></p>
        </div>
        <div class="switch-role">
            <p>Staff Member? <a href="/admin_login">Go to Admin Login</a></p>
        </div>
    </div>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Login</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:#2c3e50; display:flex; justify-content:center; align-items:center; height:100vh; color:white; }
        .card { background:#34495e; padding:40px; border-radius:12px; box-shadow:0 15px 35px rgba(0,0,0,0.3); width:100%; max-width:400px; text-align:center; border-top: 5px solid #e74c3c; }
        h2 { margin-bottom:5px; color:#fff; }
        p.sub { color: #bdc3c7; margin-bottom: 25px; font-size: 14px; }
        .form-group { margin-bottom:18px; text-align:left; }
        label { font-weight:600; display:block; margin-bottom:6px; color:#bdc3c7; }
        input { width:100%; padding:10px; border-radius:6px; border:1px solid #2c3e50; background:#2c3e50; color:white; }
        input:focus { outline: none; border-color:#e74c3c; }
        button { width:100%; padding:12px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; background:#e74c3c; color:white; margin-top:10px; }
        .flash { padding:10px; border-radius:5px; margin-bottom:15px; font-size:14px; }
        .flash.error { background:#e74c3c; color:white; }
        .switch-role { margin-top: 25px; padding-top: 15px; border-top: 1px solid #2c3e50; font-size: 13px; }
        .switch-role a { color: #4e73df; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Admin Gateway</h2>
        <p class="sub">Authorized Personnel Only</p>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form action="/admin_login" method="POST">
            <div class="form-group">
                <label>Admin Email</label>
                <input type="email" name="email" value="admin@university.edu" required>
            </div>
            <div class="form-group">
                <label>Master Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Access Dashboard</button>
        </form>
        <div class="switch-role">
            <p>Are you a student? <a href="/login">Go to Student Login</a></p>
        </div>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Student Registration</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:#f8f9fc; display:flex; justify-content:center; align-items:center; height:100vh; }
        .card { background:white; padding:40px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.08); width:100%; max-width:400px; text-align:center; border-top: 5px solid #4e73df; }
        h2 { margin-bottom:20px; color:#4e73df; }
        .form-group { margin-bottom:18px; text-align:left; }
        label { font-weight:600; display:block; margin-bottom:6px; color:#333; }
        input { width:100%; padding:10px; border-radius:6px; border:1px solid #ddd; }
        button { width:100%; padding:12px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; background:#4e73df; color:white; margin-top:10px; }
        .links { margin-top:15px; font-size:14px; }
        .links a { color:#4e73df; text-decoration:none; font-weight:bold; }
        .flash { padding:10px; border-radius:5px; margin-bottom:15px; font-size:14px; }
        .flash.error { background:#f8d7da; color:#721c24; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Create Account</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form action="/register" method="POST">
            <div class="form-group">
                <label>Full Name</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Email Address</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Register</button>
        </form>
        <div class="links">
            <p>Already have an account? <a href="/login">Login here</a></p>
        </div>
    </div>
</body>
</html>
"""

STUDENT_PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Student Complaint Portal</title>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --primary: #4e73df; --bg: #f8f9fc; --dark: #2e2e2e; }
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:var(--bg); color:var(--dark); }
        header { background:linear-gradient(135deg,var(--primary),#224abe); color:white; padding:15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .header-title { font-size: 24px; font-weight: bold; }
        .nav-links a { color: white; text-decoration: none; font-weight: bold; background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 5px; }
        .container { width:90%; max-width:800px; margin:40px auto; background:white; padding:30px; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.08); }
        h2 { margin-bottom:20px; color:var(--primary); }
        .form-group { margin-bottom:18px; }
        label { font-weight:600; display:block; margin-bottom:6px; }
        input, select, textarea { width:100%; padding:10px; border-radius:6px; border:1px solid #ddd; }
        button { padding:12px 20px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; background:var(--primary); color:white; width: 100%; font-size: 16px; }
    </style>
</head>
<body>
<header>
    <div class="header-title">Student Portal</div>
    <div class="nav-links">
        <span>Welcome, {{ user_name }}!</span>
        <a href="/logout" style="margin-left: 15px;">Logout</a>
    </div>
</header>
<div class="container">
    <h2>Submit a New Complaint</h2>
    <form id="complaintForm" action="/submit" method="POST" enctype="multipart/form-data" onsubmit="return submitForm(event)">
        <div class="form-group"><label>Full Name</label><input type="text" name="name" value="{{ user_name }}" required></div>
        <div class="form-group"><label>Student ID</label><input type="text" name="studentid" required></div>
        <div class="form-group"><label>Email Address</label><input type="email" name="email" value="{{ user_email }}" required></div>
        <div class="form-group"><label>Contact Number</label><input type="tel" name="phone"></div>
        <div class="form-group"><label>Department</label><input type="text" name="dept"></div>
        <div class="form-group">
            <label>Category</label>
            <select name="category" required>
                <option value="">Select...</option>
                <option>Academic</option>
                <option>Infrastructure</option>
                <option>Harassment</option>
                <option>Other</option>
            </select>
        </div>
        <div class="form-group"><label>Description</label><textarea name="complaint" rows="5" required></textarea></div>
        <div class="form-group"><label>Attachment (Optional)</label><input type="file" name="file"></div>
        <button type="submit">Submit Complaint</button>
    </form>
</div>
<script>
    function submitForm(event){
        event.preventDefault();
        Swal.fire({ title: "Submit?", text: "Send this complaint to admin?", icon: "question", showCancelButton: true, confirmButtonText: "Yes" })
        .then((result)=>{
            if(result.isConfirmed){
                Swal.fire({ title:"Submitted!", icon:"success", timer:1500, showConfirmButton:false });
                setTimeout(()=>{ document.getElementById('complaintForm').submit(); }, 1500);
            }
        });
    }
</script>
</body>
</html>
"""

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard</title>
    <style>
        :root { --primary: #e74c3c; --bg: #f4f6f9; --dark: #2c3e50; }
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:var(--bg); color:var(--dark); }
        header { background:var(--dark); color:white; padding:15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid var(--primary); }
        .header-title { font-size: 24px; font-weight: bold; }
        .nav-links a { color: white; text-decoration: none; font-weight: bold; background: var(--primary); padding: 8px 15px; border-radius: 5px; }
        .container { width:95%; max-width:1200px; margin:40px auto; background:white; padding:30px; border-radius:12px; box-shadow:0 5px 15px rgba(0,0,0,0.05); overflow-x: auto;}
        h2 { margin-bottom:20px; color:var(--dark); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fc; color: #333; font-weight: 600; }
        tr:hover { background-color: #f1f1f1; }
        .badge { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; background: #e3f2fd; color: #0d47a1; }
    </style>
</head>
<body>
<header>
    <div class="header-title">Admin Dashboard</div>
    <div class="nav-links">
        <span>Admin: {{ admin_name }}</span>
        <a href="/logout" style="margin-left: 15px;">Logout</a>
    </div>
</header>
<div class="container">
    <h2>All Submitted Complaints</h2>
    <table>
        <thead>
            <tr>
                <th>Student Name</th>
                <th>ID</th>
                <th>Category</th>
                <th>Department</th>
                <th>Complaint Details</th>
                <th>Attachment</th>
            </tr>
        </thead>
        <tbody>
            {% for c in complaints %}
            <tr>
                <td><strong>{{ c.Name }}</strong><br><small>{{ c.Email }}</small></td>
                <td>{{ c.StudentID }}</td>
                <td><span class="badge">{{ c.Category }}</span></td>
                <td>{{ c.Dept }}</td>
                <td>{{ c.Complaint }}</td>
                <td>{% if c.FileName %}{{ c.FileName }}{% else %}None{% endif %}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" style="text-align:center; padding: 20px;">No complaints submitted yet.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""


# --- 3. AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Email'] == email:
                    flash('Email already registered. Please log in.', 'error')
                    return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        with open(USERS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([name, email, hashed_pw])
            
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Email'] == email and check_password_hash(row['PasswordHash'], password):
                    session['user_email'] = email
                    session['user_name'] = row['Name']
                    session['role'] = 'student'
                    return redirect(url_for('student_portal'))
                    
        flash('Invalid student email or password.', 'error')
        return redirect(url_for('login'))
        
    return render_template_string(STUDENT_LOGIN_HTML)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Email'] == email and check_password_hash(row['PasswordHash'], password):
                    session['admin_email'] = email
                    session['admin_name'] = row['Name']
                    session['role'] = 'admin'
                    return redirect(url_for('admin_dashboard'))
                    
        flash('Invalid Admin Credentials.', 'error')
        return redirect(url_for('admin_login'))
        
    return render_template_string(ADMIN_LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- 4. APP ROUTES ---

@app.route('/')
def home():
    # Route traffic based on who is logged in
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session.get('role') == 'student':
        return redirect(url_for('student_portal'))
    else:
        return redirect(url_for('login'))

@app.route('/student')
def student_portal():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
        
    return render_template_string(STUDENT_PORTAL_HTML, user_name=session.get('user_name'), user_email=session.get('user_email'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    
    # Read complaints from CSV to show to the admin
    complaints_list = []
    if os.path.exists(COMPLAINTS_FILE):
        with open(COMPLAINTS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            complaints_list = list(reader)
            
    return render_template_string(ADMIN_DASHBOARD_HTML, admin_name=session.get('admin_name'), complaints=complaints_list)

@app.route('/submit', methods=['POST'])
def submit():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    name = request.form['name']
    studentid = request.form['studentid']
    email = request.form['email']
    phone = request.form['phone']
    dept = request.form['dept']
    category = request.form['category']
    complaint = request.form['complaint']

    file = request.files['file']
    filename = ""

    if file and file.filename != "":
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

    with open(COMPLAINTS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([name, studentid, email, phone, dept, category, complaint, filename])

    return redirect(url_for('student_portal'))

if __name__ == '__main__':
    app.run()
