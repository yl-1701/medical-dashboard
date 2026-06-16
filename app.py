import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import database
import payments
import auth
import os

with open(os.path.join(os.path.dirname(__file__), "running.log"), "w") as f:
    f.write(f"Active app.py loaded at {datetime.now()} from {__file__}\n")

# Page configuration
st.set_page_config(
    page_title="MediCare Clinic Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Font Override */
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Outfit', sans-serif !important;
        background-color: #090d16 !important;
        color: #f1f5f9 !important;
    }
    
    /* Title Accent */
    h1 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    
    /* Section Headers */
    h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b1329 !important;
        border-right: 1px solid #1e293b;
    }
    
    /* Premium KPI Card styling */
    .kpi-card {
        background: linear-gradient(145deg, #111a2e 0%, #0d1527 100%);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
        box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.1), 0 8px 10px -6px rgba(59, 130, 246, 0.1);
    }
    .kpi-title {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin-top: 8px;
        letter-spacing: -0.03em;
    }
    
    /* Live Queue Row Cards */
    .queue-row {
        background-color: #0e1726;
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .queue-row:hover {
        background-color: #152035;
        border-color: #3b82f6;
    }
    
    /* Streamlit Widget Enhancements */
    div[data-testid="stExpander"] {
        background-color: #0e1726 !important;
        border: 1px solid #1f293d !important;
        border-radius: 12px !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #090d16;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Enforce Authentication Gate
auth.check_inactivity_timeout()

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"
    
    if st.session_state.auth_page == "login":
        auth.show_login_screen()
    else:
        auth.show_register_screen()
    st.stop()

# 2. Main Authenticated Dashboard Layout
if "authenticated" in st.session_state and st.session_state.authenticated:
    user_role = st.session_state.user['role']
    user_patient_id = st.session_state.user['patient_id']

    st.sidebar.markdown("""
        <div style="
            display: flex; 
            align-items: center; 
            gap: 12px; 
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); 
            padding: 12px 16px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
            margin-bottom: 20px;
        ">
            <span style="font-size: 28px; color: white;">🏥</span>
            <div>
                <h2 style="margin: 0; font-size: 18px; color: white; font-weight: 700; line-height: 1.2; border-bottom: none;">MediCare</h2>
                <span style="font-size: 11px; color: #93c5fd; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">Hub Portal</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown(f"👤 **Welcome, {st.session_state.user['username']}**")
    st.sidebar.markdown(f"🔑 *Role: {user_role.capitalize()}*")
    st.sidebar.write("---")

    if user_role == "admin":
        page = st.sidebar.radio(
            "Navigation Menu",
            ["Home", "Patients", "Appointments", "Payments", "Analytics"]
        )
    else:
        page = st.sidebar.radio(
            "Patient Portal Menu",
            ["My Profile", "My Appointments", "My Payments", "Book Appointment"]
        )

    st.sidebar.write("---")
    if st.sidebar.button("Logout 🚪", use_container_width=True):
        auth.logout()

    # Load DB tables
    patients_df = database.get_all_patients()
    doctors_df = database.get_all_doctors()
    appointments_df = database.get_all_appointments_detailed()
    payments_df = database.get_all_payments_detailed()

    # Helper for status styling
    def style_appt_table(df):
        if df.empty:
            st.info("No appointments found.")
        else:
            display_df = df.copy()
            # Highlight status column
            def color_appt_status(row):
                color_map = {
                    'Scheduled': 'background-color: rgba(255, 193, 7, 0.2); color: #ffc107; font-weight: bold;',
                    'Checked-In': 'background-color: rgba(13, 202, 240, 0.2); color: #0dcaf0; font-weight: bold;',
                    'In Consultation': 'background-color: rgba(111, 66, 193, 0.2); color: #6f42c1; font-weight: bold;',
                    'Completed': 'background-color: rgba(40, 167, 69, 0.2); color: #28a745; font-weight: bold;',
                    'Cancelled': 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545; font-weight: bold;',
                    'No-Show': 'background-color: rgba(108, 117, 125, 0.2); color: #6c757d; font-weight: bold;'
                }
                status = row['Status']
                return [color_map.get(status, '') if col == 'Status' else '' for col in row.index]
                
            st.dataframe(display_df.style.apply(color_appt_status, axis=1), use_container_width=True, hide_index=True)

    # ==============================================================================
    # ADMIN FLOW
    # ==============================================================================
    if user_role == "admin":
        # --- Page: Home ---
        if page == "Home":
            st.title("🏥 MediCare Overview")
            st.markdown("Real-time clinical metrics and summary overview.")
            
            # Calculate metrics
            total_patients = len(patients_df)
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_appts = appointments_df[appointments_df['appointment_date'].str.startswith(today_str)]
            num_today = len(today_appts)
            
            upcoming_appts = appointments_df[
                (appointments_df['appointment_date'] >= today_str) & 
                (appointments_df['status'] == 'Scheduled')
            ]
            num_upcoming = len(upcoming_appts)
            
            total_revenue = payments_df[payments_df['payment_status'] == 'Paid']['amount'].sum()
            pending_payments_amt = payments_df[payments_df['payment_status'].isin(['Pending', 'Overdue'])]['amount'].sum()
            
            # Render cards
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Patients</div><div class="kpi-value">{total_patients}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">Today\'s Appointments</div><div class="kpi-value">{num_today}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">Upcoming Scheduled</div><div class="kpi-value">{num_upcoming}</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">Revenue Collected</div><div class="kpi-value">${total_revenue:,.2f}</div></div>', unsafe_allow_html=True)
            with col5:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">Pending Payments</div><div class="kpi-value" style="color: #f59e0b;">${pending_payments_amt:,.2f}</div></div>', unsafe_allow_html=True)

            st.write("---")
            
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.subheader("📅 Today's Live Queue & Agenda")
                if today_appts.empty:
                    st.info("No appointments scheduled for today.")
                else:
                    today_appts_sorted = today_appts.sort_values(by='appointment_date')
                    for _, row in today_appts_sorted.iterrows():
                        time_str = row['appointment_date'].split()[-1] if " " in row['appointment_date'] else row['appointment_date']
                        status_colors = {
                            'Scheduled': '#ffc107',
                            'Checked-In': '#0dcaf0',
                            'In Consultation': '#6f42c1',
                            'Completed': '#28a745',
                            'Cancelled': '#dc3545',
                            'No-Show': '#6c757d'
                        }
                        color = status_colors.get(row['status'], '#ffffff')
                        
                        with st.container():
                            c_info, c_action = st.columns([3, 2])
                            with c_info:
                                st.markdown(f"""
                                    <div style="padding: 10px; border-left: 4px solid {color}; background-color: #1e293b; border-radius: 4px; margin-bottom: 8px;">
                                        <span style="font-size: 14px; font-weight: bold; color: {color};">[{row['status'].upper()}]</span> 
                                        <span style="font-weight: 600; font-size: 15px; margin-left: 8px;">{row['patient_name']}</span> 
                                        <span style="color: #94a3b8; font-size: 13px;">(with {row['doctor_name']})</span><br/>
                                        <span style="font-size: 12px; color: #94a3b8; margin-top: 4px; display: inline-block;">⏰ Time: {time_str} | 📋 Reason: {row['notes'] or 'N/A'}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                            with c_action:
                                next_statuses = []
                                if row['status'] == 'Scheduled':
                                    next_statuses = [('Checked-In', '📌 Check In'), ('No-Show', '❌ No-Show')]
                                elif row['status'] == 'Checked-In':
                                    next_statuses = [('In Consultation', '🩺 Send to Doc'), ('No-Show', '❌ No-Show')]
                                elif row['status'] == 'In Consultation':
                                    next_statuses = [('Completed', '✅ Complete Visit')]
                                
                                cols = st.columns(max(len(next_statuses), 1))
                                for i, (next_status, label) in enumerate(next_statuses):
                                    if cols[i].button(label, key=f"status_btn_{row['appointment_id']}_{next_status}"):
                                        database.update_appointment_status(row['appointment_id'], next_status)
                                        st.rerun()
                                        
                                if not next_statuses:
                                    all_states = ["Scheduled", "Checked-In", "In Consultation", "Completed", "Cancelled", "No-Show"]
                                    try:
                                        curr_idx = all_states.index(row['status'])
                                    except ValueError:
                                        curr_idx = 0
                                    new_state = cols[0].selectbox(
                                        "Change Status",
                                        options=all_states,
                                        index=curr_idx,
                                        key=f"status_sel_{row['appointment_id']}",
                                        label_visibility="collapsed"
                                    )
                                    if new_state != row['status']:
                                        database.update_appointment_status(row['appointment_id'], new_state)
                                        st.rerun()
                        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    
            with col_right:
                st.subheader("🩺 On-Call Doctors")
                if doctors_df.empty:
                    st.info("No doctors registered.")
                else:
                    for _, doc in doctors_df.iterrows():
                        st.markdown(f"**{doc['full_name']}** ({doc['specialization']})  \n*Availability: {doc['availability']}*")
                        st.markdown("---")
                    
                    with st.expander("✏️ Edit Doctor Profile & Availability", expanded=False):
                        doc_choices_edit = {row['doctor_id']: row['full_name'] for _, row in doctors_df.iterrows()}
                        selected_doc_id = st.selectbox("Select Doctor to Edit", options=list(doc_choices_edit.keys()), format_func=lambda x: doc_choices_edit[x])
                        
                        if selected_doc_id:
                            doc_details = doctors_df[doctors_df['doctor_id'] == selected_doc_id].iloc[0]
                            with st.form("edit_doctor_form"):
                                doc_name_edit = st.text_input("Full Name *", value=doc_details['full_name'])
                                doc_spec_edit = st.text_input("Specialization *", value=doc_details['specialization'])
                                doc_contact_edit = st.text_input("Contact Number", value=doc_details['contact'])
                                doc_avail_edit = st.text_input("Availability Times", value=doc_details['availability'])
                                
                                submit_doc_btn = st.form_submit_button("Update Doctor Record", use_container_width=True)
                                if submit_doc_btn:
                                    if not doc_name_edit or not doc_spec_edit:
                                        st.error("Name and Specialization are required.")
                                    else:
                                        success, msg = database.update_doctor(
                                            doctor_id=selected_doc_id,
                                            full_name=doc_name_edit,
                                            specialization=doc_spec_edit,
                                            contact=doc_contact_edit,
                                            availability=doc_avail_edit
                                        )
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)

        # --- Page: Patients ---
        elif page == "Patients":
            st.title("👥 Patient Management")
            tab_view, tab_add, tab_edit_p = st.tabs(["Search & View Patients", "➕ Add New Patient", "✏️ Edit Patient Details"])
            
            with tab_view:
                st.subheader("Search Patient Records")
                search_query = st.text_input("🔍 Search patient by Name, Email or Contact", "")
                
                if not patients_df.empty:
                    if search_query:
                        filtered_patients = patients_df[
                            patients_df['full_name'].str.contains(search_query, case=False, na=False) |
                            patients_df['email'].str.contains(search_query, case=False, na=False) |
                            patients_df['contact_number'].str.contains(search_query, case=False, na=False)
                        ]
                    else:
                        filtered_patients = patients_df
                        
                    st.dataframe(filtered_patients, use_container_width=True, hide_index=True)
                    
                    # View History
                    st.write("---")
                    st.subheader("🔎 View Individual Patient History")
                    patient_choices = {row['patient_id']: f"{row['full_name']} (ID: {row['patient_id']})" for _, row in patients_df.iterrows()}
                    selected_pat_id = st.selectbox("Select Patient to view complete history:", options=list(patient_choices.keys()), format_func=lambda x: patient_choices[x])
                    
                    if selected_pat_id:
                        patient_info = patients_df[patients_df['patient_id'] == selected_pat_id].iloc[0]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Age:** {patient_info['age']}")
                            st.write(f"**Gender:** {patient_info['gender']}")
                        with col2:
                            st.write(f"**Contact:** {patient_info['contact_number']}")
                            st.write(f"**Email:** {patient_info['email']}")
                        with col3:
                            st.write(f"**Blood Group:** {patient_info['blood_group']}")
                            st.write(f"**Medical Notes:** {patient_info['medical_history']}")
                        
                        history_df = database.get_patient_history(selected_pat_id)
                        st.write("**Appointment & Payment History:**")
                        if history_df.empty:
                            st.info("No past appointment records found for this patient.")
                        else:
                            st.dataframe(history_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No patients registered yet.")
                    
            with tab_add:
                st.subheader("Add New Patient")
                with st.form("add_patient_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Full Name *")
                        age = st.number_input("Age", min_value=0, max_value=120, value=30)
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                    with col2:
                        contact = st.text_input("Contact Number *")
                        email = st.text_input("Email Address")
                        medical_history = st.text_area("Medical History Notes")
                    
                    st.write("---")
                    st.markdown("### 📅 Walk-in Appointment Setup")
                    book_immediately = st.checkbox("Book an appointment for this patient immediately?")
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        doc_choices_quick = {row['doctor_id']: f"{row['full_name']} ({row['specialization']})" for _, row in doctors_df.iterrows()}
                        quick_doctor = st.selectbox("Assign Doctor", options=list(doc_choices_quick.keys()), format_func=lambda x: doc_choices_quick[x] if doc_choices_quick else "")
                        quick_date = st.date_input("Appointment Date", value=datetime.today())
                    with col_b2:
                        quick_time = st.time_input("Appointment Time", value=datetime.now().time())
                        quick_notes = st.text_input("Reason for Visit", placeholder="e.g. Regular checkup, Follow-up")
                    
                    submit_btn = st.form_submit_button("Add Patient Record", use_container_width=True)
                    if submit_btn:
                        if not name or not contact:
                            st.error("Full Name and Contact Number are required.")
                        else:
                            if book_immediately:
                                if not quick_doctor:
                                    st.error("Please select a doctor to book the appointment.")
                                else:
                                    appt_datetime_str = f"{quick_date.strftime('%Y-%m-%d')} {quick_time.strftime('%H:%M')}"
                                    success, msg = database.add_patient_and_book_appointment(
                                        name, age, gender, contact, email, blood_group, medical_history,
                                        quick_doctor, appt_datetime_str, quick_notes if quick_notes else "Initial Consultation"
                                    )
                                    if success:
                                        st.success("Patient registered and appointment booked successfully!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            else:
                                success, msg = database.add_patient(name, age, gender, contact, email, blood_group, medical_history)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(f"Error: {msg}")

            with tab_edit_p:
                st.subheader("Edit Patient Information")
                if patients_df.empty:
                    st.info("No patients registered.")
                else:
                    patient_choices_edit = {row['patient_id']: f"{row['full_name']} (ID: {row['patient_id']})" for _, row in patients_df.iterrows()}
                    selected_pat_id_edit = st.selectbox("Select Patient to Edit", options=list(patient_choices_edit.keys()), format_func=lambda x: patient_choices_edit[x])
                    
                    if selected_pat_id_edit:
                        pat_details = patients_df[patients_df['patient_id'] == selected_pat_id_edit].iloc[0]
                        
                        with st.form("edit_patient_form"):
                            col1_p, col2_p = st.columns(2)
                            with col1_p:
                                name_edit = st.text_input("Full Name *", value=pat_details['full_name'])
                                age_edit = st.number_input("Age", min_value=0, max_value=120, value=int(pat_details['age']))
                                gender_options = ["Male", "Female", "Other"]
                                gender_idx = gender_options.index(pat_details['gender']) if pat_details['gender'] in gender_options else 0
                                gender_edit = st.selectbox("Gender", gender_options, index=gender_idx)
                                
                                blood_options = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                                blood_idx = blood_options.index(pat_details['blood_group']) if pat_details['blood_group'] in blood_options else 0
                                blood_group_edit = st.selectbox("Blood Group", blood_options, index=blood_idx)
                            with col2_p:
                                contact_edit = st.text_input("Contact Number *", value=pat_details['contact_number'])
                                email_edit = st.text_input("Email Address", value=pat_details['email'])
                                medical_history_edit = st.text_area("Medical History Notes", value=pat_details['medical_history'])
                                
                            submit_p_btn = st.form_submit_button("Update Patient Record", use_container_width=True)
                            if submit_p_btn:
                                if not name_edit or not contact_edit:
                                    st.error("Full Name and Contact Number are required.")
                                else:
                                    success, msg = database.update_patient_admin(
                                        patient_id=selected_pat_id_edit,
                                        full_name=name_edit,
                                        age=age_edit,
                                        gender=gender_edit,
                                        contact=contact_edit,
                                        email=email_edit,
                                        blood_group=blood_group_edit,
                                        history=medical_history_edit
                                    )
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

        # --- Page: Appointments ---
        elif page == "Appointments":
            st.title("📅 Appointment Management")
            st.subheader("Filter Appointments")
            
            doc_options = {"All": "All"}
            for _, row in doctors_df.iterrows():
                doc_options[row['doctor_id']] = row['full_name']
                
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sel_doctor = st.selectbox("Filter by Doctor", options=list(doc_options.keys()), format_func=lambda x: doc_options[x])
            with col_f2:
                sel_status = st.multiselect("Filter by Status", ["Scheduled", "Checked-In", "In Consultation", "Completed", "Cancelled", "No-Show"], default=["Scheduled", "Checked-In", "In Consultation", "Completed", "Cancelled", "No-Show"])
            
            filtered_appts = appointments_df.copy()
            if sel_doctor != "All":
                filtered_appts = filtered_appts[filtered_appts['doctor_id'] == sel_doctor]
            if sel_status:
                filtered_appts = filtered_appts[filtered_appts['status'].isin(sel_status)]
                
            today_date = datetime.now().date()
            def get_date_obj(date_str):
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M").date()
                except ValueError:
                    return datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
                    
            filtered_appts['date_only'] = filtered_appts['appointment_date'].apply(get_date_obj)
            
            past_appts = filtered_appts[filtered_appts['date_only'] < today_date]
            today_appts_filtered = filtered_appts[filtered_appts['date_only'] == today_date]
            future_appts = filtered_appts[filtered_appts['date_only'] > today_date]
            
            tab_today, tab_future, tab_past, tab_book, tab_edit = st.tabs([
                "Today's Appointments", "Future Appointments", "Past Appointments", "🧬 Book Appointment", "✏️ Edit / Reschedule"
            ])
            
            with tab_today:
                if not today_appts_filtered.empty:
                    display_df = today_appts_filtered[['appointment_id', 'appointment_date', 'patient_name', 'doctor_name', 'status', 'notes']].copy()
                    display_df.columns = ['ID', 'Date & Time', 'Patient Name', 'Doctor Name', 'Status', 'Notes']
                    style_appt_table(display_df)
                else:
                    st.info("No appointments scheduled for today.")
                
            with tab_future:
                if not future_appts.empty:
                    display_df = future_appts[['appointment_id', 'appointment_date', 'patient_name', 'doctor_name', 'status', 'notes']].copy()
                    display_df.columns = ['ID', 'Date & Time', 'Patient Name', 'Doctor Name', 'Status', 'Notes']
                    style_appt_table(display_df)
                else:
                    st.info("No upcoming appointments.")
                
            with tab_past:
                if not past_appts.empty:
                    display_df = past_appts[['appointment_id', 'appointment_date', 'patient_name', 'doctor_name', 'status', 'notes']].copy()
                    display_df.columns = ['ID', 'Date & Time', 'Patient Name', 'Doctor Name', 'Status', 'Notes']
                    style_appt_table(display_df)
                else:
                    st.info("No past appointments found.")
                
            with tab_book:
                st.subheader("Book New Appointment")
                if patients_df.empty or doctors_df.empty:
                    st.warning("Ensure patients and doctors exist before booking.")
                else:
                    pat_choices = {row['patient_id']: f"{row['full_name']} (ID: {row['patient_id']})" for _, row in patients_df.iterrows()}
                    doc_choices = {row['doctor_id']: f"{row['full_name']} ({row['specialization']})" for _, row in doctors_df.iterrows()}
                    
                    with st.form("book_appt_form", clear_on_submit=True):
                        patient_sel = st.selectbox("Select Patient *", options=list(pat_choices.keys()), format_func=lambda x: pat_choices[x])
                        doctor_sel = st.selectbox("Select Doctor *", options=list(doc_choices.keys()), format_func=lambda x: doc_choices[x])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            appt_date = st.date_input("Appointment Date", value=datetime.today())
                        with col2:
                            appt_time = st.time_input("Appointment Time", value=datetime.now().time())
                            
                        notes = st.text_area("Symptoms / Notes")
                        submit_btn = st.form_submit_button("Book Appointment", use_container_width=True)
                        if submit_btn:
                            appt_datetime_str = f"{appt_date.strftime('%Y-%m-%d')} {appt_time.strftime('%H:%M')}"
                            success, msg = database.book_appointment(patient_sel, doctor_sel, appt_datetime_str, "Scheduled", notes)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                                
            with tab_edit:
                st.subheader("Edit / Reschedule Existing Appointment")
                if appointments_df.empty:
                    st.info("No appointments exist to edit.")
                else:
                    appt_choices = {
                        row['appointment_id']: f"ID: {row['appointment_id']} - {row['patient_name']} (Dr. {row['doctor_name']}) on {row['appointment_date']} [{row['status']}]"
                        for _, row in appointments_df.iterrows()
                    }
                    
                    selected_appt_id = st.selectbox(
                        "Select Appointment to Edit",
                        options=list(appt_choices.keys()),
                        format_func=lambda x: appt_choices[x]
                    )
                    
                    if selected_appt_id:
                        appt_details = appointments_df[appointments_df['appointment_id'] == selected_appt_id].iloc[0]
                        
                        doctors_list = database.get_all_doctors()
                        doc_map = {row['full_name']: row['doctor_id'] for _, row in doctors_list.iterrows()}
                        default_doc_id = doc_map.get(appt_details['doctor_name'], None)
                        
                        doc_ids = [row['doctor_id'] for _, row in doctors_list.iterrows()]
                        try:
                            default_doc_idx = doc_ids.index(default_doc_id) if default_doc_id in doc_ids else 0
                        except ValueError:
                            default_doc_idx = 0
                            
                        try:
                            curr_dt = datetime.strptime(appt_details['appointment_date'], "%Y-%m-%d %H:%M")
                            curr_date = curr_dt.date()
                            curr_time = curr_dt.time()
                        except:
                            curr_date = datetime.today().date()
                            curr_time = datetime.now().time()
                            
                        with st.form("edit_appt_form"):
                            st.text_input("Patient Name", value=appt_details['patient_name'], disabled=True)
                            
                            doc_choices_edit = {row['doctor_id']: f"{row['full_name']} ({row['specialization']})" for _, row in doctors_list.iterrows()}
                            doctor_sel_edit = st.selectbox(
                                "Assigned Doctor", 
                                options=list(doc_choices_edit.keys()), 
                                format_func=lambda x: doc_choices_edit[x],
                                index=default_doc_idx
                            )
                            
                            col1_e, col2_e = st.columns(2)
                            with col1_e:
                                appt_date_edit = st.date_input("Date", value=curr_date)
                            with col2_e:
                                appt_time_edit = st.time_input("Time", value=curr_time)
                                
                            status_options = ["Scheduled", "Checked-In", "In Consultation", "Completed", "Cancelled", "No-Show"]
                            try:
                                status_idx = status_options.index(appt_details['status'])
                            except ValueError:
                                status_idx = 0
                            status_sel_edit = st.selectbox("Status", options=status_options, index=status_idx)
                            
                            notes_edit = st.text_area("Notes / Symptoms", value=appt_details['notes'])
                            
                            save_btn = st.form_submit_button("Update Appointment Details", use_container_width=True)
                            if save_btn:
                                appt_datetime_str = f"{appt_date_edit.strftime('%Y-%m-%d')} {appt_time_edit.strftime('%H:%M')}"
                                success, msg = database.update_appointment(
                                    appointment_id=selected_appt_id,
                                    doctor_id=doctor_sel_edit,
                                    appt_datetime=appt_datetime_str,
                                    status=status_sel_edit,
                                    notes=notes_edit
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

        # --- Page: Payments ---
        elif page == "Payments":
            payments.show_payments_page()

        # --- Page: Analytics ---
        elif page == "Analytics":
            st.title("📊 Clinical & Financial Analytics")
            col1, col2 = st.columns(2)
            
            if not appointments_df.empty:
                def to_month(date_str):
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    return dt.strftime("%b %Y")
                    
                appointments_df['month'] = appointments_df['appointment_date'].apply(to_month)
                
                appt_months = appointments_df.groupby('month').size().reset_index(name='appointments')
                fig_appt_month = px.bar(appt_months, x='month', y='appointments', title='Appointments per Month', color_discrete_sequence=['#3b82f6'])
                fig_appt_month.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#f8fafc')
                col1.plotly_chart(fig_appt_month, use_container_width=True)
                
                visit_counts = appointments_df.groupby('doctor_name').size().reset_index(name='visits')
                fig_doc = px.bar(visit_counts.sort_values(by='visits', ascending=True), y='doctor_name', x='visits', orientation='h', title='Most Visited Doctors', color_discrete_sequence=['#10b981'])
                fig_doc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#f8fafc')
                col2.plotly_chart(fig_doc, use_container_width=True)
            else:
                col1.info("No data for charts.")
                
            col3, col4 = st.columns(2)
            if not payments_df.empty:
                paid_payments = payments_df[payments_df['payment_status'] == 'Paid'].copy()
                if not paid_payments.empty:
                    paid_payments['date'] = pd.to_datetime(paid_payments['payment_date'])
                    paid_payments = paid_payments.sort_values(by='date')
                    paid_payments['revenue_month'] = paid_payments['date'].dt.strftime("%b %Y")
                    revenue_over_time = paid_payments.groupby('revenue_month')['amount'].sum().reset_index(name='revenue')
                    
                    fig_rev = px.line(revenue_over_time, x='revenue_month', y='revenue', title='Revenue Over Time ($)', markers=True, color_discrete_sequence=['#6366f1'])
                    fig_rev.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#f8fafc')
                    col3.plotly_chart(fig_rev, use_container_width=True)
                
                status_breakdown = payments_df.groupby('payment_status').size().reset_index(name='count')
                fig_pie = px.pie(status_breakdown, values='count', names='payment_status', title='Payment Status Breakdown', color='payment_status', color_discrete_map={'Paid': '#22c55e', 'Pending': '#f59e0b', 'Overdue': '#ef4444'})
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#f8fafc')
                col4.plotly_chart(fig_pie, use_container_width=True)

    # ==============================================================================
    # PATIENT PORTAL FLOW
    # ==============================================================================
    else:
        # Ensure patient details can be fetched
        patient_details = database.get_patient_details(user_patient_id) if user_patient_id else None
        
        if not patient_details:
            st.warning("⚠️ This user account is not linked to any registered patient record. Please contact administration.")
        else:
            # --- Page: My Profile ---
            if page == "My Profile":
                st.title("👤 My Personal Profile")
                st.markdown("Verify and edit your personal contact details and medical notes.")
                
                # Show existing profile details in a card
                st.markdown(f"""
                    <div class="kpi-card" style="margin-bottom: 20px;">
                        <h3>{patient_details['full_name']}</h3>
                        <p><b>Age:</b> {patient_details['age']} | <b>Gender:</b> {patient_details['gender']} | <b>Blood Group:</b> {patient_details['blood_group']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form("update_profile_form"):
                    st.subheader("Edit Profile Information")
                    contact_num = st.text_input("Contact Number *", value=patient_details['contact_number']).strip()
                    email_addr = st.text_input("Email Address", value=patient_details['email']).strip()
                    med_notes = st.text_area("Medical History / Personal Notes", value=patient_details['medical_history'])
                    
                    update_btn = st.form_submit_button("Update Details", use_container_width=True)
                    if update_btn:
                        if not contact_num:
                            st.error("Contact Number is required.")
                        elif not auth.validate_email(email_addr):
                            st.error("Please enter a valid email address.")
                        else:
                            success, msg = database.update_patient_profile(
                                patient_id=user_patient_id,
                                contact=contact_num,
                                email=email_addr,
                                medical_history=med_notes
                            )
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                                
            # --- Page: My Appointments ---
            elif page == "My Appointments":
                st.title("📅 My Appointments")
                st.markdown("Check your past consultations and upcoming scheduled visits.")
                
                patient_appts = database.get_patient_appointments(user_patient_id)
                if patient_appts.empty:
                    st.info("You do not have any appointment history with us yet.")
                else:
                    # Format for display
                    display_df = patient_appts[['appointment_id', 'appointment_date', 'doctor_name', 'specialization', 'status', 'notes']].copy()
                    display_df.columns = ['ID', 'Date & Time', 'Doctor', 'Specialization', 'Status', 'Notes']
                    style_appt_table(display_df)

            # --- Page: My Payments ---
            elif page == "My Payments":
                st.title("💳 My Billing & Payments")
                st.markdown("View all payments made and outstanding pending dues.")
                
                patient_pays = database.get_patient_payments(user_patient_id)
                if patient_pays.empty:
                    st.info("No billing records found.")
                else:
                    display_df = patient_pays[['payment_id', 'appointment_date', 'doctor_name', 'amount', 'payment_method', 'payment_status', 'payment_date']].copy()
                    display_df.columns = ['Payment ID', 'Appointment Date', 'Doctor', 'Amount ($)', 'Method', 'Status', 'Paid Date']
                    
                    # Highlight status column
                    def color_pay_status(row):
                        color_map = {
                            'Paid': 'background-color: rgba(40, 167, 69, 0.2); color: #28a745; font-weight: bold;',
                            'Pending': 'background-color: rgba(255, 193, 7, 0.2); color: #ffc107; font-weight: bold;',
                            'Overdue': 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545; font-weight: bold;'
                        }
                        status = row['Status']
                        return [color_map.get(status, '') if col == 'Status' else '' for col in row.index]
                        
                    st.dataframe(display_df.style.apply(color_pay_status, axis=1), use_container_width=True, hide_index=True)
                    
                    # Display total pending vs paid metrics
                    paid_sum = patient_pays[patient_pays['payment_status'] == 'Paid']['amount'].sum()
                    pending_sum = patient_pays[patient_pays['payment_status'].isin(['Pending', 'Overdue'])]['amount'].sum()
                    
                    st.write("---")
                    c1, c2 = st.columns(2)
                    c1.metric("Total Paid", f"${paid_sum:,.2f}")
                    c2.metric("Total Pending / Overdue", f"${pending_sum:,.2f}")

            # --- Page: Book Appointment ---
            elif page == "Book Appointment":
                st.title("🩺 Book a Doctor Appointment")
                st.markdown("Choose a medical specialist and select a convenient scheduling slot.")
                
                if doctors_df.empty:
                    st.warning("No doctors are currently available for booking.")
                else:
                    doc_choices = {row['doctor_id']: f"{row['full_name']} ({row['specialization']})" for _, row in doctors_df.iterrows()}
                    
                    with st.form("patient_book_appt_form", clear_on_submit=True):
                        doctor_sel = st.selectbox("Select Specialist *", options=list(doc_choices.keys()), format_func=lambda x: doc_choices[x])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            appt_date = st.date_input("Preferred Date", value=datetime.today())
                        with col2:
                            appt_time = st.time_input("Preferred Time", value=datetime.now().time())
                            
                        notes = st.text_area("Brief Symptoms / Reasons for Appointment")
                        submit_btn = st.form_submit_button("Request Booking", use_container_width=True)
                        
                        if submit_btn:
                            appt_datetime_str = f"{appt_date.strftime('%Y-%m-%d')} {appt_time.strftime('%H:%M')}"
                            success, msg = database.book_appointment(
                                patient_id=user_patient_id,
                                doctor_id=doctor_sel,
                                appt_datetime=appt_datetime_str,
                                status="Scheduled",
                                notes=notes
                            )
                            if success:
                                st.success("Appointment successfully booked! Please view 'My Appointments' tab for updates.")
                            else:
                                st.error(msg)
