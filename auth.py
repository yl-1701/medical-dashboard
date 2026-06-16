import streamlit as st
import bcrypt
import re
from datetime import datetime
import database

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hashed value."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def check_inactivity_timeout():
    """Verify session inactivity. Auto-logout after 30 minutes of inactivity."""
    timeout_minutes = 30
    if "authenticated" in st.session_state and st.session_state.authenticated:
        if "last_activity" in st.session_state:
            last_activity = st.session_state.last_activity
            elapsed = (datetime.now() - last_activity).total_seconds()
            if elapsed > (timeout_minutes * 60):
                logout(timeout=True)
        # Update activity timestamp on interaction
        st.session_state.last_activity = datetime.now()

def logout(timeout=False):
    """Log out of the session."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.last_activity = None
    if timeout:
        st.session_state.logout_message = "Logged out due to 30 minutes of inactivity."
    else:
        st.session_state.logout_message = "Logged out successfully."
    st.rerun()

def validate_email(email):
    if not email:
        return True # Email is optional in database schema
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email) is not None

def show_login_screen():
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h2>🏥 MediCare Hub Portal</h2>
            <p style='color: #8c7e72;'>Please sign in to access your dashboard</p>
        </div>
    """, unsafe_allow_html=True)
    
    if "logout_message" in st.session_state and st.session_state.logout_message:
        st.info(st.session_state.logout_message)
        del st.session_state.logout_message

    with st.form("login_form"):
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In", use_container_width=True)

        if login_btn:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                user = database.get_user_by_username(username)
                if user and verify_password(password, user['password_hash']):
                    # Login successful
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.last_activity = datetime.now()
                    
                    # Update last login in db
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    database.update_last_login(user['user_id'], now_str)
                    
                    st.success("Successfully logged in!")
                    st.rerun()
                else:
                    # Generic error for security
                    st.error("Invalid username or password.")

    st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
    if st.button("New Patient? Create an account here"):
        st.session_state.auth_page = "register"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def show_register_screen():
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h2>📝 Patient Registration</h2>
            <p style='color: #8c7e72;'>Register to schedule appointments and view your medical records</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        st.subheader("Login Information")
        username = st.text_input("Choose Username *").strip()
        password = st.text_input("Password * (Min 8 characters)", type="password")
        confirm_password = st.text_input("Confirm Password *", type="password")

        st.subheader("Personal Details")
        full_name = st.text_input("Full Name *").strip()
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with col2:
            blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            contact = st.text_input("Contact Number *").strip()

        email = st.text_input("Email Address").strip()
        medical_history = st.text_area("Medical History Notes (Optional)")

        register_btn = st.form_submit_button("Register & Create Account", use_container_width=True)

        if register_btn:
            if not username or not password or not confirm_password or not full_name or not contact:
                st.error("All fields marked with * are required.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif not validate_email(email):
                st.error("Please enter a valid email address.")
            elif not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
                st.error("Username must be between 3 and 20 alphanumeric/underscore characters.")
            else:
                hashed = hash_password(password)
                success, msg = database.create_user_and_patient(
                    username=username,
                    password_hash=hashed,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    contact=contact,
                    email=email,
                    blood_group=blood_group,
                    medical_history=medical_history
                )
                if success:
                    st.success("Account created successfully! Please log in.")
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
    if st.button("Already have an account? Sign In"):
        st.session_state.auth_page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
