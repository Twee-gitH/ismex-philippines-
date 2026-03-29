import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# --- 1. THE CENTRAL REGISTRY (DATABASE) ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_to_registry(name, pin):
    registry = load_registry()
    if name in registry:
        return False, "User already exists. Please Sign In."
    registry[name] = {
        "pin": pin,
        "wallet_balance": 0.0,
        "investments": [],
        "transactions": []
    }
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)
    return True, "Success"

def update_user_data(name, data):
    registry = load_registry()
    registry[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)

# --- 2. THEMED DESIGN ---
st.set_page_config(page_title="BPSM Official", page_icon="🇵🇭", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .cover-card {
        background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .id-label { font-size: 0.7rem; color: #666; font-weight: bold; margin-bottom: -15px; }
    .stButton>button { border-radius: 10px; height: 3.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION FLOW ---
if 'active_user' not in st.session_state:
    st.session_state.active_user = None

if st.session_state.active_user is None:
    # --- COVER DESIGN ---
    st.markdown("""
        <div class="cover-card">
            <h1 style='margin:0;'>BAGONG PILIPINAS</h1>
            <p style='letter-spacing:3px; opacity:0.9;'>STOCK MARKET PORTAL</p>
            <hr style='opacity:0.3;'>
            <p style='font-size:0.9rem;'>Official Digital Trading Floor</p>
        </div>
        """, unsafe_allow_html=True)

    auth_tab, reg_tab = st.tabs(["🔑 SECURE SIGN-IN", "📝 REGISTER I.D."])

    with auth_tab:
        st.markdown("<p class='id-label'>INVESTOR FULL NAME</p>", unsafe_allow_html=True)
        login_name = st.text_input("name_id", label_visibility="collapsed").upper()
        
        st.markdown("<p class='id-label'>6-DIGIT SECURITY PIN</p>", unsafe_allow_html=True)
        login_pin = st.text_input("pin_id", type="password", max_chars=6, label_visibility="collapsed")
        
        if st.button("VERIFY & ENTER", use_container_width=True):
            registry = load_registry()
            if login_name in registry and registry[login_name]['pin'] == login_pin:
                st.session_state.active_user = login_name
                st.rerun()
            else:
                st.error("Invalid Credentials. Please check your Name or PIN.")

    with reg_tab:
        st.write("### Create Official Investor ID")
        new_name = st.text_input("FULL NAME (AS PER GOVT I.D.)").upper()
        new_pin = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        confirm_pin = st.text_input("CONFIRM PIN", type="password", max_chars=6)
        
        if st.button("REGISTER ACCOUNT", use_container_width=True):
            if len(new_pin) != 6 or not new_pin.isdigit():
                st.error("PIN must be exactly 6 digits.")
            elif new_pin != confirm_pin:
                st.error("PINs do not match.")
            elif new_name:
                success, msg = save_user_to_registry(new_name, new_pin)
                if success:
                    st.success("Account Created! You can now Sign In.")
                else:
                    st.warning(msg)

# --- 4. THE DASHBOARD (LOGGED IN) ---
else:
    current_username = st.session_state.active_user
    # Pull fresh data from registry
    registry = load_registry()
    user_data = registry[current_username]

    st.markdown(f"### 🇵🇭 Welcome, {current_username}")
    
    # [Calculations for Matured Profits]
    now = datetime.now()
    total_matured = 0.0
    active_inv = 0.0
    
    for inv in user_data['investments']:
        release = datetime.fromisoformat(inv['release_time'])
        if now >= release:
            total_matured += (inv['amount'] + inv['profit'])
        else:
            active_inv += inv['amount']
    
    liquid_bal = user_data['wallet_balance'] + total_matured

    # UI Metrics
    m1, m2 = st.columns(2)
    m1.metric("AVAILABLE CASH", f"₱{liquid_bal:,.2f}")
    m2.metric("IN MARKET", f"₱{active_inv:,.2f}")

    # Operations
    tab1, tab2, tab3 = st.tabs(["📊 TRADE", "💳 WALLET", "📜 HISTORY"])

    with tab1:
        st.write("#### Open New Stock Position")
        amt = st.number_input("Purchase Amount", min_value=500.0, step=500.0)
        if st.button("EXECUTE TRADE"):
            if liquid_bal >= amt:
                new_trade = {
                    "amount": amt, "profit": amt * 0.20,
                    "start_time": datetime.now().isoformat(),
                    "release_time": (datetime.now() + timedelta(hours=24)).isoformat()
                }
                user_data['investments'].append(new_trade)
                # Deduct from wallet balance
                if user_data['wallet_balance'] >= amt:
                    user_data['wallet_balance'] -= amt
                update_user_data(current_username, user_data)
                st.success("Trade Successful!")
                st.rerun()
            else:
                st.error("Insufficient Funds.")

    with tab2:
        st.write("#### Deposit Proof")
        d_amt = st.number_input("Amount Sent", min_value=100.0)
        ref = st.text_input("Reference No.")
        if st.button("SUBMIT DEPOSIT"):
            user_data['transactions'].append({"type": "DEP", "amt": d_amt, "status": "PENDING", "ref": ref, "date": str(now)})
            update_user_data(current_username, user_data)
            st.toast("Admin notified.")

    with tab3:
        if user_data['transactions']:
            st.table(pd.DataFrame(user_data['transactions'])[['type', 'amt', 'status']])

    if st.sidebar.button("LOGOUT"):
        st.session_state.active_user = None
        st.rerun()

    time.sleep(10)
    st.rerun()
    
