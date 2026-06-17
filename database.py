import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medical.db")

def get_raw_connection():
    """Returns (connection, is_postgres)"""
    if "postgres" in st.secrets:
        import psycopg2
        pg_config = st.secrets["postgres"]
        if "url" in pg_config:
            conn = psycopg2.connect(pg_config["url"])
        else:
            conn = psycopg2.connect(
                host=pg_config.get("host"),
                database=pg_config.get("database", "postgres"),
                user=pg_config.get("user", "postgres"),
                password=pg_config.get("password"),
                port=pg_config.get("port", 5432),
                sslmode='require'
            )
        return conn, True
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn, False

def get_connection():
    # Legacy connection fallback: returns raw connection
    conn, is_pg = get_raw_connection()
    return conn

def query_one(query, params=None):
    conn, is_pg = get_raw_connection()
    cursor = conn.cursor()
    if is_pg:
        query = query.replace("?", "%s")
    if params is not None and not isinstance(params, (tuple, list)):
        params = (params,)
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row and is_pg:
        colnames = [desc[0] for desc in cursor.description]
        row = dict(zip(colnames, row))
    conn.close()
    return row

def query_all(query, params=None):
    conn, is_pg = get_raw_connection()
    cursor = conn.cursor()
    if is_pg:
        query = query.replace("?", "%s")
    if params is not None and not isinstance(params, (tuple, list)):
        params = (params,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if is_pg:
        colnames = [desc[0] for desc in cursor.description]
        rows = [dict(zip(colnames, r)) for r in rows]
    conn.close()
    return rows

def execute_write(query, params=None, returning_id=False):
    conn, is_pg = get_raw_connection()
    cursor = conn.cursor()
    if is_pg:
        query = query.replace("?", "%s")
    if params is not None and not isinstance(params, (tuple, list)):
        params = (params,)
    cursor.execute(query, params)
    result = None
    if returning_id:
        row = cursor.fetchone()
        if row:
            result = row[0]
    conn.commit()
    conn.close()
    return result

def read_dataframe(query, params=None):
    conn, is_pg = get_raw_connection()
    if is_pg:
        query = query.replace("?", "%s")
    if params is not None and not isinstance(params, (tuple, list)):
        params = (params,)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def init_db():
    """Initialize the database locally if empty. Skipped if postgres cloud mode is active."""
    if "postgres" in st.secrets:
        return
    conn, is_pg = get_raw_connection()
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

# Initialize local SQLite DB if not running in PostgreSQL cloud mode
init_db()

# --- Patient Database Queries ---
def add_patient(name, age, gender, contact, email, blood_group, history):
    try:
        execute_write("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, gender, contact, email, blood_group, history))
        return True, "Patient added successfully!"
    except Exception as e:
        return False, str(e)

def get_all_patients():
    return read_dataframe("SELECT * FROM patients")

def get_patient_history(patient_id):
    query = """
        SELECT a.appointment_id, a.appointment_date, d.full_name as doctor_name, 
               d.specialization, a.status, a.notes, p.amount, p.payment_status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN payments p ON a.appointment_id = p.appointment_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """
    return read_dataframe(query, patient_id)

# --- Doctor Database Queries ---
def get_all_doctors():
    return read_dataframe("SELECT * FROM doctors")

# --- Appointment Database Queries ---
def book_appointment(patient_id, doctor_id, appt_datetime, status, notes):
    try:
        execute_write("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, appt_datetime, status, notes))
        return True, "Appointment booked successfully!"
    except Exception as e:
        return False, str(e)

def update_appointment_status(appointment_id, status):
    try:
        execute_write("UPDATE appointments SET status = ? WHERE appointment_id = ?", (status, appointment_id))
        return True, "Appointment status updated!"
    except Exception as e:
        return False, str(e)

def update_appointment(appointment_id, doctor_id, appt_datetime, status, notes):
    try:
        execute_write("""
            UPDATE appointments
            SET doctor_id = ?, appointment_date = ?, status = ?, notes = ?
            WHERE appointment_id = ?
        """, (doctor_id, appt_datetime, status, notes, appointment_id))
        return True, "Appointment updated successfully!"
    except Exception as e:
        return False, str(e)

def auto_update_no_shows():
    """Automatically update Scheduled appointments to No-Show if they are past 15 minutes of slot time."""
    try:
        rows = query_all("SELECT appointment_id, appointment_date FROM appointments WHERE status = 'Scheduled'")
        now = datetime.now()
        for row in rows:
            appt_id = row['appointment_id']
            appt_date_str = row['appointment_date']
            try:
                # Format: YYYY-MM-DD HH:MM
                appt_dt = datetime.strptime(appt_date_str, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    # Fallback for YYYY-MM-DD
                    appt_dt = datetime.strptime(appt_date_str.split()[0], "%Y-%m-%d")
                except:
                    continue
            
            # Check if 15 minutes have passed since the slot start time
            if now > appt_dt + timedelta(minutes=15):
                execute_write("UPDATE appointments SET status = 'No-Show' WHERE appointment_id = ?", (appt_id,))
        return True
    except Exception as e:
        return False

def get_all_appointments_detailed():
    auto_update_no_shows()
    query = """
        SELECT a.appointment_id, a.appointment_date, a.status, a.notes,
               p.patient_id, p.full_name as patient_name, p.contact_number as patient_contact,
               d.doctor_id, d.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC
    """
    return read_dataframe(query)

# --- Payment Database Queries ---
def get_all_payments_detailed():
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
    return read_dataframe(query)

def record_payment(appointment_id, amount, method, status, payment_date):
    try:
        execute_write("""
            INSERT INTO payments (appointment_id, amount, payment_method, payment_status, payment_date)
            VALUES (?, ?, ?, ?, ?)
        """, (appointment_id, amount, method, status, payment_date))
        return True, "Payment recorded successfully!"
    except Exception as e:
        return False, str(e)

def get_unpaid_appointments():
    query = """
        SELECT a.appointment_id, a.appointment_date, p.full_name as patient_name, d.full_name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN payments pay ON a.appointment_id = pay.appointment_id
        WHERE pay.payment_id IS NULL
        ORDER BY a.appointment_date DESC
    """
    return read_dataframe(query)

# --- Auth and Patient Profile Database Queries ---
def get_user_by_username(username):
    row = query_one("SELECT * FROM users WHERE username = ?", (username,))
    return row

def update_last_login(user_id, time_str):
    try:
        execute_write("UPDATE users SET last_login = ? WHERE user_id = ?", (time_str, user_id))
        return True
    except Exception as e:
        return False

def update_username_and_password(user_id, new_username, new_password_hash=None):
    try:
        if new_password_hash:
            execute_write("""
                UPDATE users
                SET username = ?, password_hash = ?
                WHERE user_id = ?
            """, (new_username, new_password_hash, user_id))
        else:
            execute_write("""
                UPDATE users
                SET username = ?
                WHERE user_id = ?
            """, (new_username, user_id))
        return True, "Profile details updated successfully!"
    except Exception as e:
        if "UNIQUE" in str(e) or "duplicate key" in str(e).lower():
            return False, "Username already exists. Please choose a different one."
        return False, str(e)

def create_user_and_patient(username, password_hash, full_name, age, gender, contact, email, blood_group, medical_history):
    try:
        # 1. Insert patient and fetch new ID
        patient_id = execute_write("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING patient_id
        """, (full_name, age, gender, contact, email, blood_group, medical_history), returning_id=True)
        
        # 2. Insert user mapping to patient
        created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_write("""
            INSERT INTO users (patient_id, username, password_hash, role, created_at)
            VALUES (?, ?, ?, 'patient', ?)
        """, (patient_id, username, password_hash, created_at_str))
        
        return True, "Account created successfully!"
    except Exception as e:
        if "UNIQUE" in str(e) or "duplicate key" in str(e).lower():
            return False, "Username already exists. Please choose a different one."
        return False, str(e)

def update_patient_profile(patient_id, contact, email, medical_history):
    try:
        execute_write("""
            UPDATE patients
            SET contact_number = ?, email = ?, medical_history = ?
            WHERE patient_id = ?
        """, (contact, email, medical_history, patient_id))
        return True, "Profile updated successfully!"
    except Exception as e:
        return False, str(e)

def get_patient_details(patient_id):
    return query_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))

def get_patient_appointments(patient_id):
    query = """
        SELECT a.appointment_id, a.appointment_date, a.status, a.notes,
               d.full_name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
    """
    return read_dataframe(query, patient_id)

def get_patient_payments(patient_id):
    query = """
        SELECT pay.payment_id, pay.amount, pay.payment_method, pay.payment_status, pay.payment_date,
               a.appointment_date, d.full_name as doctor_name
        FROM payments pay
        JOIN appointments a ON pay.appointment_id = a.appointment_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY pay.payment_id DESC
    """
    return read_dataframe(query, patient_id)

# --- Admin CRUD Update Operations ---
def update_patient_admin(patient_id, full_name, age, gender, contact, email, blood_group, history):
    try:
        execute_write("""
            UPDATE patients
            SET full_name = ?, age = ?, gender = ?, contact_number = ?, email = ?, blood_group = ?, medical_history = ?
            WHERE patient_id = ?
        """, (full_name, age, gender, contact, email, blood_group, history, patient_id))
        return True, "Patient details updated successfully!"
    except Exception as e:
        return False, str(e)

def update_doctor(doctor_id, full_name, specialization, contact, availability):
    try:
        execute_write("""
            UPDATE doctors
            SET full_name = ?, specialization = ?, contact = ?, availability = ?
            WHERE doctor_id = ?
        """, (full_name, specialization, contact, availability, doctor_id))
        return True, "Doctor details updated successfully!"
    except Exception as e:
        return False, str(e)

def update_payment(payment_id, amount, payment_method, payment_status, payment_date):
    try:
        execute_write("""
            UPDATE payments
            SET amount = ?, payment_method = ?, payment_status = ?, payment_date = ?
            WHERE payment_id = ?
        """, (amount, payment_method, payment_status, payment_date, payment_id))
        return True, "Payment details updated successfully!"
    except Exception as e:
        return False, str(e)

def add_patient_and_book_appointment(name, age, gender, contact, email, blood_group, history, doctor_id, appt_datetime, notes):
    try:
        patient_id = execute_write("""
            INSERT INTO patients (full_name, age, gender, contact_number, email, blood_group, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING patient_id
        """, (name, age, gender, contact, email, blood_group, history), returning_id=True)
        
        execute_write("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, 'Scheduled', ?)
        """, (patient_id, doctor_id, appt_datetime, notes))
        
        return True, "Patient registered and appointment booked successfully!"
    except Exception as e:
        return False, str(e)
