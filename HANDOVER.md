# Handover Documentation: MediCare Clinic Dashboard

This guide explains how to install, run, back up, and deploy the MediCare Clinic Dashboard for daily operations.

---

## 📋 System Requirements
- A computer with **Python 3.8 or newer** installed.
- Internet connection (for installing dependencies initially).
- Modern web browser (Chrome, Edge, Firefox, or Safari).

---

## 🚀 Deployment Options

### Option A: Local Network Deployment (Highly Recommended)
You can run the application on one main computer (acting as the server) in the clinic, and other staff members (receptionist, doctors, patients) can access the system from their own computers, tablets, or phones on the same Wi-Fi network.

#### Step 1: Run the App on the Server
1. Copy the project folder to the server computer.
2. Double-click the **`run_dashboard.bat`** file.
   - *This will automatically set up Python dependencies and launch the application.*

#### Step 2: Access from other Clinic Devices
When the server starts, you will see output in the command window like:
```text
  Local URL: http://localhost:8501
  Network URL: http://192.168.1.50:8501
```
- Tell other devices on the clinic Wi-Fi network to open their browser and visit the **Network URL** (e.g. `http://192.168.1.50:8501`).
- Keep the server computer's command window open during clinic hours.

---

### Option B: Cloud Hosting (Free & Accessible Anywhere)
If you want the dashboard to be accessible over the internet (outside the clinic building), you can deploy it to **Streamlit Community Cloud** for free.

1. Create a free account at [Streamlit Share](https://share.streamlit.io/).
2. Connect your GitHub account.
3. Select this repository (`yl-1701/medical-dashboard`).
4. Set Main File Path to: `app.py`.
5. Click **Deploy**. The app will be live on a secure, public web link (e.g., `https://medicare-dashboard.streamlit.app`).

---

## 💾 Database Maintenance & Backups
All clinic data (patient profiles, doctor schedules, queue states, billing transactions) is saved in the **`medical.db`** file in the project folder.

### How to back up data:
- Simply make a copy of the **`medical.db`** file and save it to an external drive, USB stick, or secure cloud folder (like Google Drive or OneDrive) at the end of each day.
- To restore the database in case of computer failure, just place your backed-up `medical.db` file back into the project folder.

---

## 🔑 Default Accounts (Admin Settings)
On first load, the database creates the following default logins:

| Role | Username | Default Password | Notes |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@1234` | Change username/password in **Settings** page |
| **Patient Profile** | `patient1` | `Patient@1234` | Linked to demo patient John Doe |
