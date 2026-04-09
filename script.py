import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# 1. DATABASE SETUP
try:
    creds_info = st.secrets["firebase"]
    creds = service_account.Credentials.from_service_account_info(creds_info)
    db = firestore.Client(credentials=creds)
except Exception as e:
    st.error("Database connection failed.")

def load_registry():
    try:
        return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
    except:
        return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# 2. STATE MANAGEMENT
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'action_type' not in st.session_state: st.session_state.action_type = None

# 3. PAGE CONFIG & CSS
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    header, footer, .stDeployButton { visibility: hidden; }
    .stApp { background-color: #0e1117; color: white; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; border-left: 5px solid #00ff88; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 4. ADMIN LOGIC
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
    reg = load_registry()
    for username, u_data in reg.items():
        for idx, action in enumerate(list(u_data.get('pending_actions', []))):
            with st.expander(f"{action['type']} - {username}"):
                if st.button("APPROVE", key=f"a_{username}_{idx}"):
                    # Approval Logic
                    if action['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()

# 5. USER DASHBOARD
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    
    st.write(f"User: {st.session_state.user}")
    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

    st.markdown(f'<div class="balance-box"><h1>₱{wallet:,.2f}</h1></div>', unsafe_allow_html=True)

    # REINVEST Logic
    if st.button("♻️ REINVEST"):
        if wallet >= 500:
            data['wallet'] -= wallet
            data.setdefault('inv', []).append({"amount": wallet, "start_time": datetime.now().isoformat()})
            update_user(st.session_state.user, data); st.rerun()

    # ACTIVE INVESTMENTS
    for idx, inv in enumerate(data.get('inv', [])):
        st.info(f"Active Capital: ₱{inv['amount']}")

# 6. LANDING & LOGIN
elif st.session_state.page == "login":
    u = st.text_input("NAME").upper()
    p = st.text_input("PIN", type="password")
    if st.button("ENTER"):
        reg = load_registry()
        if u in reg and str(reg[u]['pin']) == str(p):
            st.session_state.user = u; st.rerun()
else:
    st.title("INTERNATIONAL STOCK MARKET EXCHANGE")
    if st.button("LOGIN / REGISTER"): st.session_state.page = "login"; st.rerun()
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
    if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
  
