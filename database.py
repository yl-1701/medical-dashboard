import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medical.db")

def get_connection():
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables and sample data if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create Patients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        contact_number TEXT,
        email TEXT,
        blood_group TEXT,
        medical_history TEXT
    )
    """)

    # Create Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        contact TEXT,
        availability TEXT
    )
    """)

    # Create Appointments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date TEXT, -- YYYY-MM-DD HH:MM
        status TEXT DEFAULT 'Scheduled', -- Scheduled, Completed, Cancelled
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
    )
    """)

    # Create Payments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        amount REAL,
        payment_method TEXT, -- Cash, Card, UPI
        payment_status TEXT DEFAULT 'Pending', -- Paid, Pending, Overdue
        payment_date TEXT, -- YYYY-MM-DD
        FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id)
    )
    """)

    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NULLABLE,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- admin, patient
        created_at TEXT,
        last_login TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
    )
    """)

    conn.commit()

    # Check if doctors already exist to decide whether to populate mock data
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        # Pre-populate sample doctors
        doctors = [
            ("Dr. Alice Smith", "Cardiology", "+1-555-0199", "Mon, Wed, Fri (9 AM - 2 PM)"),
            ("Dr. Bob Jones", "Pediatrics", "+1-555-0188", "Tue, Thu (10 AM - 4 PM)"),
            ("Dr. Carol Vance", "Dermatology", "+1-555-0177", "Mon-Thu (1 PM - 6 PM)")
        ]
        cursor.executemany("INSERT INTO doctors (full_name, specialization, contact, availability) VALUES (?, ?, ?, ?)", doctors)

        # Pre-populate sample patients (at least 5)
        patients = [
            ("John Doe", 45, "Male", "+1-555-0111", "john.doe@example.com", "A+", "Hypertension, mild asthma"),
            ("Jane Miller", 34, "Female", "+1-555-0222", "jane.m@example.com", "O-", "No chronic conditions, seasonal allergies"),
            ("Robert Chen", 29, "Male", "+1-555-0333", "robert.c@example.com", "B+", "Type 2 Diabetes controlled by diet"),
            ("Emily Davis", 62, "Female", "+1-555-0444", "emily.d@example.com", "AB+", "Osteoarthritis in left knee"),
            ("Michael Brown", 8, "Male", "+1-555-0555", "m.brown@example.com", "O+", "Pre-existing eczema")
        ]
        cursor.executemany("INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history) VALUES (?, ?, ?, ?, ?, ?, ?)", patients)
        
        # Pre-populate sample appointments (at least 10)
        today = datetime.now()
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        past_week_str = (today - timedelta(days=6)).strftime("%Y-%m-%d")

        appointments = [
            (1, 1, f"{past_week_str} 10:00", "Completed", "Routine checkup, blood pressure stable."),
            (2, 2, f"{past_week_str} 11:30", "Completed", "Follow-up on skin rash."),
            (3, 1, f"{yesterday_str} 09:30", "Completed", "Cardiology follow-up."),
            (5, 2, f"{yesterday_str} 14:00", "Cancelled", "Patient rescheduled."),
            (4, 3, f"{today_str} 10:00", "Scheduled", "Dermatology initial consultation."),
            (1, 2, f"{today_str} 11:30", "Scheduled", "Check heart rate fluctuations."),
            (2, 1, f"{today_str} 15:00", "Scheduled", "General consultation for headache."),
            (3, 3, f"{tomorrow_str} 10:30", "Scheduled", "Follow-up session."),
            (5, 2, f"{tomorrow_str} 11:00", "Scheduled", "Child vaccination check."),
            (4, 1, f"{next_week_str} 09:00", "Scheduled", "Regular checkup.")
        ]
        cursor.executemany("INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes) VALUES (?, ?, ?, ?, ?)", appointments)

        # Pre-populate sample payments (at least 8)
        payments = [
            (1, 150.0, "Cash", "Paid", past_week_str),
            (2, 120.0, "Card", "Paid", past_week_str),
            (3, 200.0, "UPI", "Paid", yesterday_str),
            (4, 80.0, "Cash", "Pending", ""),
            (5, 120.0, "UPI", "Paid", today_str),
            (6, 150.0, "Card", "Pending", ""),
            (7, 100.0, "UPI", "Pending", ""),
            (8, 200.0, "Card", "Overdue", "")
        ]
        cursor.executemany("INSERT INTO payments (appointment_id, amount, payment_method, payment_status, payment_date) VALUES (?, ?, ?, ?, ?)", payments)
        
        conn.commit()

    # Separately ensure the users table has the default accounts seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        import bcrypt
        admin_pwd_hash = bcrypt.hashpw(b"Admin@1234", bcrypt.gensalt()).decode('utf-8')
        patient_pwd_hash = bcrypt.hashpw(b"Patient@1234", bcrypt.gensalt()).decode('utf-8')
        
        created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (patient_id, username, password_hash, role, created_at)
            VALUES (NULL, 'admin', ?, 'admin', ?)
        """, (admin_pwd_hash, created_at_str))
        
        # Check if John Doe (patient_id = 1) exists, otherwise default to NULL
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id = 1")
        has_pat_1 = cursor.fetchone()
        pid = 1 if has_pat_1 else None
        
        cursor.execute("""
            INSERT INTO users (patient_id, username, password_hash, role, created_at)
            VALUES (?, 'patient1', ?, 'patient', ?)
        """, (pid, patient_pwd_hash, created_at_str))
        
        conn.commit()
    
    conn.close()

# Initialize DB on import
init_db()

# --- Patient Database Queries ---
def add_patient(name, age, gender, contact, email, blood_group, history):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, gender, contact, email, blood_group, history))
        conn.commit()
        conn.close()
        return True, "Patient added successfully!"
    except Exception as e:
        return False, str(e)

def get_all_patients():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    conn.close()
    return df

def get_patient_history(patient_id):
    conn = get_connection()
    query = """
        SELECT a.appointment_id, a.appointment_date, d.full_name as doctor_name, 
               d.specialization, a.status, a.notes, p.amount, p.payment_status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN payments p ON a.appointment_id = p.appointment_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(patient_id,))
    conn.close()
    return df

# --- Doctor Database Queries ---
def get_all_doctors():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM doctors", conn)
    conn.close()
    return df

# --- Appointment Database Queries ---
def book_appointment(patient_id, doctor_id, appt_datetime, status, notes):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, appt_datetime, status, notes))
        conn.commit()
        conn.close()
        return True, "Appointment booked successfully!"
    except Exception as e:
        return False, str(e)

def update_appointment_status(appointment_id, status):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?", (status, appointment_id))
        conn.commit()
        conn.close()
        return True, "Appointment status updated!"
    except Exception as e:
        return False, str(e)

def update_appointment(appointment_id, doctor_id, appt_datetime, status, notes):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments
            SET doctor_id = ?, appointment_date = ?, status = ?, notes = ?
            WHERE appointment_id = ?
        """, (doctor_id, appt_datetime, status, notes, appointment_id))
        conn.commit()
        conn.close()
        return True, "Appointment updated successfully!"
    except Exception as e:
        return False, str(e)

def get_all_appointments_detailed():
    conn = get_connection()
    query = """
        SELECT a.appointment_id, a.appointment_date, a.status, a.notes,
               p.patient_id, p.full_name as patient_name, p.contact_number as patient_contact,
               d.doctor_id, d.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Payment Database Queries ---
def get_all_payments_detailed():
    conn = get_connection()
    query = """
        SELECT pay.payment_id, pay.appointment_id, pay.amount, pay.payment_method, 
               pay.payment_status, pay.payment_date,
               a.appointment_date, pat.full_name as patient_name, d.full_name as doctor_name
        FROM payments pay
        JOIN appointments a ON pay.appointment_id = a.appointment_id
        JOIN patients pat ON a.patient_id = pat.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY pay.payment_id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def record_payment(appointment_id, amount, method, status, payment_date):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO payments (appointment_id, amount, payment_method, payment_status, payment_date)
            VALUES (?, ?, ?, ?, ?)
        """, (appointment_id, amount, method, status, payment_date))
        conn.commit()
        conn.close()
        return True, "Payment recorded successfully!"
    except Exception as e:
        return False, str(e)

def get_unpaid_appointments():
    conn = get_connection()
    # Find appointments that do not have a payment associated with them
    query = """
        SELECT a.appointment_id, a.appointment_date, p.full_name as patient_name, d.full_name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN payments pay ON a.appointment_id = pay.appointment_id
        WHERE pay.payment_id IS NULL
        ORDER BY a.appointment_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Auth and Patient Profile Database Queries ---
def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def update_last_login(user_id, time_str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (time_str, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def create_user_and_patient(username, password_hash, full_name, age, gender, contact, email, blood_group, medical_history):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Insert patient
        cursor.execute("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (full_name, age, gender, contact, email, blood_group, medical_history))
        patient_id = cursor.lastrowid
        
        # 2. Insert user mapping to patient
        created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (patient_id, username, password_hash, role, created_at)
            VALUES (?, ?, ?, 'patient', ?)
        """, (patient_id, username, password_hash, created_at_str))
        
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose a different one."
    except Exception as e:
        return False, str(e)

def update_patient_profile(patient_id, contact, email, medical_history):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients
            SET contact_number = ?, email = ?, medical_history = ?
            WHERE patient_id = ?
        """, (contact, email, medical_history, patient_id))
        conn.commit()
        conn.close()
        return True, "Profile updated successfully!"
    except Exception as e:
        return False, str(e)

def get_patient_details(patient_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    if patient:
        return dict(patient)
    return None

def get_patient_appointments(patient_id):
    conn = get_connection()
    query = """
        SELECT a.appointment_id, a.appointment_date, a.status, a.notes,
               d.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(patient_id,))
    conn.close()
    return df

def get_patient_payments(patient_id):
    conn = get_connection()
    query = """
        SELECT pay.payment_id, pay.amount, pay.payment_method, pay.payment_status, pay.payment_date,
               a.appointment_date, d.full_name as doctor_name
        FROM payments pay
        JOIN appointments a ON pay.appointment_id = a.appointment_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY pay.payment_id DESC
    """
    df = pd.read_sql_query(query, conn, params=(patient_id,))
    conn.close()
    return df

# --- Admin CRUD Update Operations ---
def update_patient_admin(patient_id, full_name, age, gender, contact, email, blood_group, history):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients
            SET full_name = ?, age = ?, gender = ?, contact_number = ?, email = ?, blood_group = ?, medical_history = ?
            WHERE patient_id = ?
        """, (full_name, age, gender, contact, email, blood_group, history, patient_id))
        conn.commit()
        conn.close()
        return True, "Patient details updated successfully!"
    except Exception as e:
        return False, str(e)

def update_doctor(doctor_id, full_name, specialization, contact, availability):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE doctors
            SET full_name = ?, specialization = ?, contact = ?, availability = ?
            WHERE doctor_id = ?
        """, (full_name, specialization, contact, availability, doctor_id))
        conn.commit()
        conn.close()
        return True, "Doctor details updated successfully!"
    except Exception as e:
        return False, str(e)

def update_payment(payment_id, amount, payment_method, payment_status, payment_date):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE payments
            SET amount = ?, payment_method = ?, payment_status = ?, payment_date = ?
            WHERE payment_id = ?
        """, (amount, payment_method, payment_status, payment_date, payment_id))
        conn.commit()
        conn.close()
        return True, "Payment details updated successfully!"
    except Exception as e:
        return False, str(e)

def add_patient_and_book_appointment(name, age, gender, contact, email, blood_group, history, doctor_id, appt_datetime, notes):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, gender, contact, email, blood_group, history))
        patient_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, 'Scheduled', ?)
        """, (patient_id, doctor_id, appt_datetime, notes))
        
        conn.commit()
        conn.close()
        return True, "Patient registered and appointment booked successfully!"
    except Exception as e:
        return False, str(e)


