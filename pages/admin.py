import streamlit as st
import json
import os

# --- 1. SESSION INITIALIZER (CRITICAL FIX) ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# --- 2. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_all(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- 3. ADMIN UI ---
st.set_page_config(page_title="BPSM ADMIN", layout="wide")

# Sidebar Login
st.sidebar.title("🔐 Admin Access")
admin_pw = st.sidebar.text_input("Enter Admin Key", type="password")

if admin_pw == "MASTER123": # <--- You can change this password here
    st.title("👨‍💼 BPSM MASTER CONTROL")
    reg = load_registry()

    # Mobile-friendly Tabs
    tab1, tab2, tab3 = st.tabs(["🔔 APPROVALS", "🛠️ ADJUST", "👥 USERS"])

    with tab1:
        st.subheader("📥 Pending Deposits")
        found_dep = False
        for user, d in reg.items():
            for i, tx in enumerate(d.get('tx', [])):
                if tx['type'] == 'DEP' and tx['status'] == 'PENDING':
                    found_dep = True
                    st.warning(f"Investor: {user} | Amount: ₱{tx['amt']:,}")
                    if st.button(f"Approve {user}", key=f"app_{user}_{i}"):
                        reg[user]['wallet'] += tx['amt']
                        reg[user]['tx'][i]['status'] = 'APPROVED'
                        save_all(reg)
                        st.rerun()
        if not found_dep: st.write("No pending deposits.")

    with tab2:
        st.subheader("🛠️ Quick Balance Edit")
        if reg:
            target = st.selectbox("Select User", list(reg.keys()))
            amount = st.number_input("Amount (PHP)", min_value=1.0, step=100.0)
            mode = st.radio("Action", ["Add (+)", "Deduct (-)"])
            if st.button("Apply Change"):
                if mode == "Add (+)": reg[target]['wallet'] += amount
                else: reg[target]['wallet'] -= amount
                save_all(reg)
                st.success(f"Updated {target} successfully!")
        else: st.write("No users registered.")

    with tab3:
        st.subheader("👥 User Directory")
        for user, d in reg.items():
            with st.expander(f"👤 {user} (₱{d['wallet']:,.2f})"):
                st.write(f"**PIN:** `{d['pin']}`")
                st.write("**Recent History:**")
                st.write(d.get('tx', []))
else:
    st.info("Enter Admin Key in the sidebar to open the dashboard.")
    
