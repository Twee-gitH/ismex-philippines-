import streamlit as st
import time
import json
import os
from datetime import datetime, timedelta

# --- 1. DATA PERSISTENCE (THE "DATABASE") ---
DB_FILE = "user_data.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return None

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, default=str)

# --- 2. APP CONFIG & STYLE ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭", layout="centered")

st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #0038a8;
        color: white;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0038a8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION INITIALIZATION ---
if 'user' not in st.session_state:
    st.session_state.user = load_data()

# --- 4. SIGNUP PAGE ---
if st.session_state.user is None:
    st.markdown("<h2 style='text-align: center;'>🇵🇭 INVESTOR REGISTRATION</h2>", unsafe_allow_html=True)
    full_name = st.text_input("FULL NAME").upper()
    reg_pin = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
    
    if st.button("CREATE SECURE ACCOUNT"):
        if full_name and len(reg_pin) == 6 and reg_pin.isdigit():
            user_data = {
                "name": full_name,
                "pin": reg_pin,
                "deposits": []
            }
            save_data(user_data)
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("PIN MUST BE EXACTLY 6 DIGITS")

# --- 5. DASHBOARD PAGE ---
else:
    user = st.session_state.user
    st.markdown(f"### MABUHAY, {user['name']}! 👋")
    
    # Logic: Only count profit if time has passed
    total_principal = sum(d['amount'] for d in user['deposits'])
    matured_profit = 0
    pending_profit = 0
    
    for d in user['deposits']:
        release_time = datetime.fromisoformat(d['release_time'])
        if datetime.now() >= release_time:
            matured_profit += d['profit']
        else:
            pending_profit += d['profit']

    current_balance = total_principal + matured_profit

    # Dashboard Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><b>AVAILABLE BALANCE</b><br><h2>₱{current_balance:,.2f}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><b>PENDING GROWTH</b><br><h2 style="color:#f59e0b;">₱{pending_profit:,.2f}</h2></div>', unsafe_allow_html=True)

    st.divider()

    # --- NEW INVESTMENT ---
    with st.expander("📥 START NEW INVESTMENT", expanded=True):
        amounts = [500, 1000, 5000, 10000, 20000, 50000]
        selected_amt = st.selectbox("CHOOSE PESO AMOUNT", amounts)
        if st.button(f"CONFIRM ₱{selected_amt:,} DEPOSIT"):
            new_dep = {
                "amount": float(selected_amt),
                "start_time": datetime.now().isoformat(),
                "release_time": (datetime.now() + timedelta(hours=24)).isoformat(),
                "profit": float(selected_amt) * 0.20
            }
            user['deposits'].append(new_dep)
            save_data(user)
            st.success("INVESTMENT ACTIVATED!")
            st.rerun()

    # --- ACTIVE INVESTMENTS WITH PROGRESS BARS ---
    st.subheader("⏳ PORTFOLIO GROWTH")
    if not user['deposits']:
        st.info("No active investments. Start one above!")
    else:
        for i, d in enumerate(user['deposits']):
            start = datetime.fromisoformat(d['start_time'])
            end = datetime.fromisoformat(d['release_time'])
            now = datetime.now()
            
            total_duration = (end - start).total_seconds()
            elapsed = (now - start).total_seconds()
            progress = min(max(elapsed / total_duration, 0.0), 1.0)

            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"**Principal: ₱{d['amount']:,}**")
                col_b.write(f"**+ ₱{d['profit']:,}**")
                
                st.progress(progress)
                
                if progress < 1.0:
                    remaining = end - now
                    hrs, mins = divmod(int(remaining.total_seconds()), 3600)
                    st.caption(f"🕒 Maturity in {hrs}h {mins//60}m")
                else:
                    st.write("✅ **PROFIT ADDED TO BALANCE**")

    # --- WITHDRAWAL ---
    st.divider()
    st.subheader("📤 WITHDRAW FUNDS")
    w_amt = st.number_input("AMOUNT TO WITHDRAW", min_value=0.0, step=100.0)
    w_pin = st.text_input("VERIFY PIN", type="password", max_chars=6)

    if st.button("REQUEST WITHDRAWAL"):
        if w_amt < 500:
            st.error("MINIMUM WITHDRAWAL IS ₱500")
        elif w_amt > current_balance:
            st.error("INSUFFICIENT BALANCE")
        elif w_pin != user['pin']:
            st.error("INVALID PIN")
        else:
            st.balloons()
            st.success("REQUEST SENT! ADMIN WILL PROCESS WITHIN 24H.")

    if st.button("RESET ACCOUNT (LOGOUT)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.user = None
        st.rerun()

    # --- AUTO-REFRESH SCRIPT ---
    # This keeps the progress bars moving every 60 seconds
    time.sleep(60)
    st.rerun()
            
