import streamlit as st
import pandas as pd
from datetime import datetime
import database

def show_payments_page():
    st.title("💳 Payment Records Management")
    st.markdown("Track patient payments, record transactions, and manage outstanding balances.")

    # Load data once at the top — all calls use @st.cache_data so repeated reruns are near-instant
    payments_df_all = database.get_all_payments_detailed()

    # Custom styling
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 1.5rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Record New Payment Form
    with st.expander("➕ Record New Payment", expanded=False):
        st.subheader("New Payment Transaction")
        
        # Get appointments that do not have payments recorded yet or we can allow paying for any appointment
        unpaid_df = database.get_unpaid_appointments()
        
        appt_options = {}
        if unpaid_df.empty:
            st.info("No unpaid appointments found. All existing appointments have payments recorded.")
            # Reuse the already-loaded payments_df_all to derive all appointments
            all_appts = database.get_all_appointments_detailed()
            if not all_appts.empty:
                for _, row in all_appts.iterrows():
                    d_name = row['doctor_name']
                    d_str = d_name if d_name.lower().startswith("dr.") else f"Dr. {d_name}"
                    appt_options[row['appointment_id']] = f"Appt ID: {row['appointment_id']} - {row['patient_name']} ({d_str}) on {row['appointment_date']}"
        else:
            for _, row in unpaid_df.iterrows():
                d_name = row['doctor_name']
                d_str = d_name if d_name.lower().startswith("dr.") else f"Dr. {d_name}"
                appt_options[row['appointment_id']] = f"Appt ID: {row['appointment_id']} - {row['patient_name']} ({d_str}) on {row['appointment_date']}"

        if not appt_options:
            st.warning("Please create appointments first before recording payments.")
        else:
            with st.form("record_payment_form", clear_on_submit=True):
                selected_appt_id = st.selectbox(
                    "Select Appointment",
                    options=list(appt_options.keys()),
                    format_func=lambda x: appt_options[x]
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("Amount ($)", min_value=0.0, step=10.0, value=100.0)
                    payment_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI"])
                with col2:
                    payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Overdue"])
                    payment_date = st.date_input("Payment Date", value=datetime.today())
                
                submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)
                
                if submit_btn:
                    p_date_str = payment_date.strftime("%Y-%m-%d") if payment_status == "Paid" else ""
                    success, msg = database.record_payment(
                        appointment_id=selected_appt_id,
                        amount=amount,
                        method=payment_method,
                        status=payment_status,
                        payment_date=p_date_str
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")

    # 1b. Edit Existing Payment Form
    with st.expander("✏️ Edit Existing Payment", expanded=False):
        st.subheader("Edit Payment Record")
        payments_df_edit = payments_df_all  # reuse the pre-loaded DataFrame
        if payments_df_edit.empty:
            st.info("No payment records exist to edit.")
        else:
            pay_options = {}
            for _, row in payments_df_edit.iterrows():
                pay_options[row['payment_id']] = f"Payment ID: {row['payment_id']} - {row['patient_name']} (${row['amount']}) [{row['payment_status']}]"
                
            selected_pay_id = st.selectbox(
                "Select Transaction to Edit",
                options=list(pay_options.keys()),
                format_func=lambda x: pay_options[x]
            )
            if selected_pay_id:
                pay_details = payments_df_edit[payments_df_edit['payment_id'] == selected_pay_id].iloc[0]
                
                with st.form("edit_payment_form"):
                    st.text_input("Patient Name", value=pay_details['patient_name'], disabled=True)
                    st.text_input("Assigned Doctor", value=pay_details['doctor_name'], disabled=True)
                    st.text_input("Appointment Date", value=pay_details['appointment_date'], disabled=True)
                    
                    col1_p, col2_p = st.columns(2)
                    with col1_p:
                        amount_edit = st.number_input("Amount ($)", min_value=0.0, step=10.0, value=float(pay_details['amount']))
                        method_options = ["Cash", "Card", "UPI"]
                        method_idx = method_options.index(pay_details['payment_method']) if pay_details['payment_method'] in method_options else 0
                        method_edit = st.selectbox("Payment Method", method_options, index=method_idx)
                    with col2_p:
                        status_options = ["Paid", "Pending", "Overdue"]
                        status_idx = status_options.index(pay_details['payment_status']) if pay_details['payment_status'] in status_options else 0
                        status_edit = st.selectbox("Payment Status", status_options, index=status_idx)
                        
                        try:
                            default_p_date = datetime.strptime(pay_details['payment_date'], "%Y-%m-%d").date() if pay_details['payment_date'] else datetime.today().date()
                        except:
                            default_p_date = datetime.today().date()
                        date_edit = st.date_input("Payment Date", value=default_p_date)
                        
                    save_pay_btn = st.form_submit_button("Update Payment Details", use_container_width=True)
                    if save_pay_btn:
                        p_date_str = date_edit.strftime("%Y-%m-%d") if status_edit == "Paid" else ""
                        success, msg = database.update_payment(
                            payment_id=selected_pay_id,
                            amount=amount_edit,
                            payment_method=method_edit,
                            payment_status=status_edit,
                            payment_date=p_date_str
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # 2. Payments Table & Filters
    st.subheader("Transaction History")
    
    payments_df = payments_df_all  # reuse the pre-loaded DataFrame
    
    if payments_df.empty:
        st.info("No payment records found.")
    else:
        # Filter controls
        col1, col2 = st.columns([1, 2])
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=["Paid", "Pending", "Overdue"],
                default=["Paid", "Pending", "Overdue"]
            )
        with col2:
            search_query = st.text_input("🔍 Search by Patient or Doctor Name", "")

        # Apply filters
        filtered_df = payments_df[payments_df['payment_status'].isin(status_filter)]
        
        if search_query:
            filtered_df = filtered_df[
                filtered_df['patient_name'].str.contains(search_query, case=False, na=False) |
                filtered_df['doctor_name'].str.contains(search_query, case=False, na=False)
            ]

        if filtered_df.empty:
            st.warning("No records match the current filters.")
        else:
            # Let's map styling to dataframe
            def style_status(row):
                color_map = {
                    'Paid': 'background-color: rgba(40, 167, 69, 0.2); color: #28a745; font-weight: bold;',
                    'Pending': 'background-color: rgba(255, 193, 7, 0.2); color: #ffc107; font-weight: bold;',
                    'Overdue': 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545; font-weight: bold;'
                }
                status = row['Status']
                return [color_map.get(status, '') if col == 'Status' else '' for col in row.index]

            # Reorder columns for display
            display_df = filtered_df[[
                'payment_id', 'patient_name', 'doctor_name', 'appointment_date', 
                'amount', 'payment_method', 'payment_status', 'payment_date'
            ]].copy()
            
            display_df.columns = [
                'Payment ID', 'Patient', 'Doctor', 'Appointment Date', 
                'Amount ($)', 'Method', 'Status', 'Paid Date'
            ]
            
            # Format Amount Column
            styled_df = display_df.style.apply(style_status, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Brief Summary
            total_amt = filtered_df['amount'].sum()
            paid_amt = filtered_df[filtered_df['payment_status'] == 'Paid']['amount'].sum()
            pending_amt = filtered_df[filtered_df['payment_status'] == 'Pending']['amount'].sum()
            overdue_amt = filtered_df[filtered_df['payment_status'] == 'Overdue']['amount'].sum()
            
            st.write("---")
            col_tot, col_paid, col_pend, col_over = st.columns(4)
            col_tot.metric("Selected Total", f"${total_amt:,.2f}")
            col_paid.metric("Paid", f"${paid_amt:,.2f}")
            col_pend.metric("Pending", f"${pending_amt:,.2f}")
            col_over.metric("Overdue", f"${overdue_amt:,.2f}")

            # 3. Generate Printable Invoice
            st.write("---")
            st.subheader("🧾 Generate Patient Invoice / Receipt")
            
            with st.expander("Generate Printable Invoice", expanded=False):
                invoice_options = {
                    row['payment_id']: f"Inv #{row['payment_id']} - {row['patient_name']} (${row['amount']}) on {row['appointment_date']}"
                    for _, row in filtered_df.iterrows()
                }
                if not invoice_options:
                    st.info("No transaction records found.")
                else:
                    selected_inv_id = st.selectbox(
                        "Select Payment Record for Invoice",
                        options=list(invoice_options.keys()),
                        format_func=lambda x: invoice_options[x]
                    )
                    
                    if selected_inv_id:
                        inv_data = filtered_df[filtered_df['payment_id'] == selected_inv_id].iloc[0]
                        status_badge_color = "#28a745" if inv_data['payment_status'] == 'Paid' else "#ffc107" if inv_data['payment_status'] == 'Pending' else "#dc3545"
                        
                        invoice_html = f"""
                        <div style="background-color: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #eae2d5; color: #2c241e; font-family: sans-serif; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px -1px rgba(44, 37, 30, 0.05);">
                            <!-- Header -->
                            <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #eae2d5; padding-bottom: 15px;">
                                <div>
                                    <h2 style="margin: 0; color: #8c6239;">🏥 MEDICARE CLINIC</h2>
                                    <span style="font-size: 12px; color: #8c7e72;">123 Healthcare Blvd, Suite 100</span><br/>
                                    <span style="font-size: 12px; color: #8c7e72;">Phone: +1-555-0100 | support@medicare.com</span>
                                </div>
                                <div style="text-align: right;">
                                    <h3 style="margin: 0; color: #2c241e;">INVOICE / RECEIPT</h3>
                                    <span style="font-size: 13px; color: #8c7e72;"><b>Invoice #:</b> {inv_data['payment_id']}</span><br/>
                                    <span style="font-size: 13px; color: #8c7e72;"><b>Date:</b> {inv_data['payment_date'] or datetime.now().strftime('%Y-%m-%d')}</span>
                                </div>
                            </div>
                            
                            <!-- Body Info -->
                            <div style="margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                <div>
                                    <h4 style="margin: 0 0 5px 0; color: #8c7e72; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;">Billed To:</h4>
                                    <strong style="font-size: 15px;">{inv_data['patient_name']}</strong><br/>
                                    <span style="font-size: 13px; color: #8c7e72;">Patient ID: {inv_data['appointment_id']}</span>
                                </div>
                                <div style="text-align: right; font-size: 13px;">
                                    <h4 style="margin: 0 0 5px 0; color: #8c7e72; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;">Service Details:</h4>
                                    <strong style="font-size: 14px;">{inv_data['doctor_name']}</strong><br/>
                                    <span style="font-size: 13px; color: #8c7e72;">Date: {inv_data['appointment_date']}</span>
                                </div>
                            </div>
                            
                            <!-- Invoice Table -->
                            <table style="width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 14px;">
                                <thead>
                                    <tr style="border-bottom: 2px solid #eae2d5;">
                                        <th style="text-align: left; padding: 10px 0; color: #8c7e72;">Description</th>
                                        <th style="text-align: right; padding: 10px 0; color: #8c7e72;">Amount</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="border-bottom: 1px solid #eae2d5;">
                                        <td style="padding: 12px 0;">Consultation Fee / Medical Services</td>
                                        <td style="text-align: right; padding: 12px 0;">${inv_data['amount']:.2f}</td>
                                    </tr>
                                    <tr style="font-weight: bold; border-top: 2px solid #eae2d5;">
                                        <td style="padding: 12px 0; font-size: 15px;">Total Due</td>
                                        <td style="text-align: right; padding: 12px 0; font-size: 15px; color: #8c6239;">${inv_data['amount']:.2f}</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <!-- Payment Status Footer -->
                            <div style="margin-top: 30px; display: flex; justify-content: space-between; align-items: center; background-color: #faf7f2; padding: 12px 20px; border-radius: 6px; border: 1px solid #eae2d5;">
                                <div>
                                    <span style="font-size: 12px; color: #8c7e72;">Payment Method</span><br/>
                                    <strong style="font-size: 14px; color: #2c241e;">{inv_data['payment_method']}</strong>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size: 12px; color: #8c7e72;">Status</span><br/>
                                    <span style="background-color: {status_badge_color}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                                        {inv_data['payment_status'].upper()}
                                    </span>
                                </div>
                            </div>
                        </div>
                        """
                        
                        st.markdown(invoice_html, unsafe_allow_html=True)
                        st.write("")
                        
                        st.download_button(
                            label="📥 Download Invoice Text / Receipt",
                            data=f"INVOICE #{inv_data['payment_id']}\nClinic: MediCare\nPatient: {inv_data['patient_name']}\nDoctor: {inv_data['doctor_name']}\nDate: {inv_data['appointment_date']}\nAmount: ${inv_data['amount']:.2f}\nStatus: {inv_data['payment_status']}\nMethod: {inv_data['payment_method']}",
                            file_name=f"Invoice_{inv_data['payment_id']}_{inv_data['patient_name']}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

