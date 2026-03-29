import streamlit as st
import json
import os

# --- 1. DATA ENGINE ---
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

# --- 2. SECURE LOGIN ---
st.set_page_config(page_title="BPSM ADMIN", layout="wide")

# This box appears in the sidebar on mobile
admin_pw = st.sidebar.text_input("Admin Key", type="password")

if admin_pw == "MASTER123":
    st.title("👨‍💼 BPSM MASTER CONTROL")
    reg = load_registry()
    
    if not reg:
        st.info("No users have registered yet.")
    else:
        st.subheader("👥 Investor Directory")
        for user, d in reg.items():
            with st.expander(f"👤 {user} | Balance: ₱{d['wallet']:,.2f}"):
                st.write(f"**PIN:** {d['pin']}")
                if st.button(f"Add ₱1,000 to {user}", key=f"btn_{user}"):
                    reg[user]['wallet'] += 1000
                    save_all(reg)
                    st.rerun()
else:
    st.warning("Please enter the Admin Key in the sidebar to access this page.")
    
