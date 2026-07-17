"""
Sarvajnaya Dashboard - Streamlit App
Features:
- View all clients with fields: name, GMB_profile, social_profiles (comma separated), service_start_date, service_end_date, potential_prospect (bool), payment_status, remaining_payment, reminder_date, remarks
- Prospects follow-up pipeline
- Add new client / add new prospect (name, phone, source, followup_date, remark, status)
- Simple reminder indicator
- Uses SQLite for storage (file: sarvajnaya.db)

Run: pip install streamlit pandas
Then: streamlit run sarvajnaya_dashboard.py
"""

import sqlite3
from datetime import datetime, date
import pandas as pd
import streamlit as st

DB_FILE = "sarvajnaya.db"

# ---------- DB helpers ----------

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        gmb_profile TEXT,
        social_profiles TEXT,
        service_start_date TEXT,
        service_end_date TEXT,
        potential INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'Not Paid',
        remaining_payment REAL DEFAULT 0,
        reminder_date TEXT,
        remarks TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        source TEXT,
        followup_date TEXT,
        remark TEXT,
        status TEXT DEFAULT 'New'
    )
    ''')

    conn.commit()
    conn.close()


# ---------- Data operations ----------

def add_client(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO clients (name, phone, gmb_profile, social_profiles, service_start_date, service_end_date, potential, payment_status, remaining_payment, reminder_date, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name'), data.get('phone'), data.get('gmb_profile'), data.get('social_profiles'),
        data.get('service_start_date'), data.get('service_end_date'), int(data.get('potential', 0)),
        data.get('payment_status'), float(data.get('remaining_payment') or 0), data.get('reminder_date'), data.get('remarks')
    ))
    conn.commit()
    conn.close()


def update_client_payment(client_id: int, payment_status: str, remaining: float, reminder_date: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        UPDATE clients SET payment_status=?, remaining_payment=?, reminder_date=? WHERE id=?
    ''', (payment_status, remaining, reminder_date, client_id))
    conn.commit()
    conn.close()


def get_clients_df():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM clients', conn, parse_dates=['service_start_date', 'service_end_date', 'reminder_date'])
    conn.close()
    return df


def add_prospect(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO prospects (name, phone, source, followup_date, remark, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data.get('name'), data.get('phone'), data.get('source'), data.get('followup_date'), data.get('remark'), data.get('status')))
    conn.commit()
    conn.close()


def get_prospects_df():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM prospects', conn, parse_dates=['followup_date'])
    conn.close()
    return df


def update_prospect_status(pid: int, status: str, followup_date: str = None, remark: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        UPDATE prospects SET status=?, followup_date=?, remark=? WHERE id=?
    ''', (status, followup_date, remark, pid))
    conn.commit()
    conn.close()


def delete_client(client_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM clients WHERE id=?', (client_id,))
    conn.commit()
    conn.close()


def delete_prospect(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM prospects WHERE id=?', (pid,))
    conn.commit()
    conn.close()


# ---------- Utility ----------

def parse_date(val):
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    try:
        return datetime.strptime(val, "%Y-%m-%d").date().isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(val).date().isoformat()
        except Exception:
            return None


# ---------- Streamlit UI ----------

st.set_page_config(page_title="Sarvajnaya Dashboard", layout="wide")

init_db()

st.title("Sarvajnaya — Client & Prospect Dashboard")

# Sidebar actions
st.sidebar.header("Actions")
view = st.sidebar.selectbox("Choose view", ["Overview", "Clients", "Prospects", "Add Client", "Add Prospect", "Settings"])

if view == "Overview":
    st.header("Overview")

    clients_df = get_clients_df()
    prospects_df = get_prospects_df()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clients", len(clients_df))

    if not clients_df.empty:
        active_mask = clients_df['service_end_date'].isnull() | (clients_df['service_end_date'] >= pd.Timestamp(date.today()))
        active_count = int(active_mask.sum())
        open_payments = int((clients_df['payment_status'] != 'Paid').sum())
    else:
        active_count = 0
        open_payments = 0

    col2.metric("Active Contracts", active_count)
    col3.metric("Open Payments", open_payments)

    if not prospects_df.empty:
        open_prospects = int(prospects_df['status'].isin(['New', 'Follow-up']).sum())
    else:
        open_prospects = 0
    col4.metric("Open Prospects", open_prospects)

    st.subheader("Upcoming Reminders (next 7 days)")
    if not clients_df.empty:
        clients_df['reminder_date_dt'] = pd.to_datetime(clients_df['reminder_date'], errors='coerce')
        soon = clients_df[
            (clients_df['reminder_date_dt'] >= pd.Timestamp(date.today())) &
            (clients_df['reminder_date_dt'] <= pd.Timestamp(date.today()) + pd.Timedelta(days=7))
        ]
        if soon.empty:
            st.write("No reminders in the next 7 days.")
        else:
            st.dataframe(soon[['id', 'name', 'phone', 'gmb_profile', 'remaining_payment', 'reminder_date', 'remarks']], use_container_width=True)
    else:
        st.write("No clients yet.")

    st.subheader("All Clients")
    if not clients_df.empty:
        st.dataframe(clients_df.drop(columns=['reminder_date_dt'], errors='ignore'), use_container_width=True)
    else:
        st.write("No client data to show")

elif view == "Clients":
    st.header("Clients — All Profiles & Status")
    df = get_clients_df()
    if df.empty:
        st.info("No clients yet — use 'Add Client' in the sidebar")
    else:
        with st.expander("Filters"):
            q_name = st.text_input("Search name or phone")
            only_open_payments = st.checkbox("Only show open payments", value=False)
            only_active = st.checkbox("Only active services", value=False)

        display_df = df.copy()
        if q_name:
            name_match = display_df['name'].astype(str).str.contains(q_name, case=False, na=False)
            phone_match = display_df['phone'].astype(str).str.contains(q_name, case=False, na=False)
            display_df = display_df[name_match | phone_match]
        if only_open_payments:
            display_df = display_df[display_df['payment_status'] != 'Paid']
        if only_active:
            today_ts = pd.Timestamp(date.today())
            display_df = display_df[(display_df['service_end_date'].isnull()) | (display_df['service_end_date'] >= today_ts)]

        st.dataframe(display_df, use_container_width=True)

        st.subheader("Update payment / reminder for a client")
        with st.form("payment_form"):
            client_ids = df['id'].tolist()
            c_id = st.selectbox("Client", options=client_ids, format_func=lambda x: f"{x} - {df.loc[df['id'] == x, 'name'].values[0]}")
            p_status = st.selectbox("Payment status", ['Not Paid', 'Partial', 'Paid'])
            remaining = st.number_input("Remaining amount", min_value=0.0, value=0.0, format="%.2f")
            r_date = st.date_input("Reminder date (optional)", value=None)
            submitted = st.form_submit_button("Update")
            if submitted:
                rd_iso = parse_date(r_date) if r_date else None
                update_client_payment(c_id, p_status, remaining, rd_iso)
                st.success("Updated client payment/reminder")
                st.rerun()

        st.subheader("Delete a client")
        with st.form("delete_client_form"):
            del_id = st.selectbox("Client to delete", options=client_ids, format_func=lambda x: f"{x} - {df.loc[df['id'] == x, 'name'].values[0]}", key="del_client")
            confirm = st.checkbox("I confirm I want to delete this client")
            del_submit = st.form_submit_button("Delete")
            if del_submit:
                if confirm:
                    delete_client(del_id)
                    st.success("Client deleted")
                    st.rerun()
                else:
                    st.warning("Please check the confirmation box to delete")

elif view == "Prospects":
    st.header("Prospects & Follow-up Pipeline")
    df = get_prospects_df()
    if df.empty:
        st.info("No prospects recorded yet.")
    else:
        st.dataframe(df, use_container_width=True)

        st.subheader("Manage prospect status")
        with st.form("prospect_update"):
            pids = df['id'].tolist()
            pid = st.selectbox("Prospect", options=pids, format_func=lambda x: f"{x} - {df.loc[df['id'] == x, 'name'].values[0]}")
            new_status = st.selectbox("Status", ['New', 'Follow-up', 'Contacted', 'Converted', 'Lost'])
            new_follow = st.date_input("Next followup date", value=None)
            new_remark = st.text_input("Remark")
            ok = st.form_submit_button("Update Prospect")
            if ok:
                follow_iso = parse_date(new_follow) if new_follow else None
                update_prospect_status(pid, new_status, follow_iso, new_remark)
                st.success("Prospect updated")
                st.rerun()

        st.subheader("Delete a prospect")
        with st.form("delete_prospect_form"):
            del_pid = st.selectbox("Prospect to delete", options=pids, format_func=lambda x: f"{x} - {df.loc[df['id'] == x, 'name'].values[0]}", key="del_prospect")
            confirm_p = st.checkbox("I confirm I want to delete this prospect")
            del_p_submit = st.form_submit_button("Delete")
            if del_p_submit:
                if confirm_p:
                    delete_prospect(del_pid)
                    st.success("Prospect deleted")
                    st.rerun()
                else:
                    st.warning("Please check the confirmation box to delete")

elif view == "Add Client":
    st.header("Add New Client")
    with st.form("add_client_form"):
        name = st.text_input("Client Name")
        phone = st.text_input("Phone")
        gmb = st.text_input("GMB Profile URL")
        socials = st.text_area("Social Profiles (comma separated)")
        start = st.date_input("Service Start Date", value=None)
        end = st.date_input("Service End Date", value=None)
        potential = st.checkbox("Potential Prospect?", value=False)
        payment_status = st.selectbox("Payment status", ['Not Paid', 'Partial', 'Paid'])
        remaining_payment = st.number_input("Remaining payment", min_value=0.0, value=0.0, format="%.2f")
        reminder = st.date_input("Reminder Date (optional)", value=None)
        remarks = st.text_area("Remarks")
        submit = st.form_submit_button("Add Client")
        if submit:
            if not name:
                st.error("Name is required")
            else:
                data = {
                    'name': name,
                    'phone': phone,
                    'gmb_profile': gmb,
                    'social_profiles': socials,
                    'service_start_date': parse_date(start),
                    'service_end_date': parse_date(end),
                    'potential': int(potential),
                    'payment_status': payment_status,
                    'remaining_payment': remaining_payment,
                    'reminder_date': parse_date(reminder),
                    'remarks': remarks
                }
                add_client(data)
                st.success(f"Client '{name}' added")

elif view == "Add Prospect":
    st.header("Add New Prospect / Lead")
    with st.form("add_prospect_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        source = st.text_input("Approached by (source)")
        followup = st.date_input("Follow-up Date", value=None)
        remark = st.text_area("Remark")
        status = st.selectbox("Status", ['New', 'Follow-up', 'Contacted', 'Converted', 'Lost'])
        add_ok = st.form_submit_button("Add Prospect")
        if add_ok:
            if not name:
                st.error("Name is required")
            else:
                data = {
                    'name': name,
                    'phone': phone,
                    'source': source,
                    'followup_date': parse_date(followup),
                    'remark': remark,
                    'status': status
                }
                add_prospect(data)
                st.success(f"Prospect '{name}' added")

elif view == "Settings":
    st.header("Settings & Export")
    st.write("Export data to CSV for offline use")
    clients_export_df = get_clients_df()
    prospects_export_df = get_prospects_df()

    csv = clients_export_df.to_csv(index=False)
    st.download_button("Download clients.csv", csv, file_name="clients.csv", mime='text/csv')

    csv2 = prospects_export_df.to_csv(index=False)
    st.download_button("Download prospects.csv", csv2, file_name="prospects.csv", mime='text/csv')


# Footer / quick tips
st.markdown("---")
st.caption("Sarvajnaya Dashboard — built with Streamlit. Customize fields as needed. Backups: copy the 'sarvajnaya.db' file.")
