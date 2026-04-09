import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import json

# 1. DATABASE CONNECTION WITH MOBILE-FRIENDLY ERROR HANDLING
try:
    if "firebase" in st.secrets:
        # We manually clean the private key to prevent TOML formatting crashes
        raw_key = st.secrets["firebase"]["private_key"]
        fixed_key = raw_key.replace("\\n", "\n")
        
        creds_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": fixed_key,
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=creds)
    else:
        st.error("MISSING SECRETS: Go to Settings > Secrets and add your [firebase] block.")
except Exception as e:
    st.error(f"DATABASE CRASH: {e}")

# Logic Helpers
def load_registry():
    try:
        users_ref = db.collection("investors")
        return {doc.id: doc.to_dict() for doc in users_ref.stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State initialization
for key, val in [('page','ad'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

# 2. THE FULL UI & INTERFACE
st.set_page_config(page_title="ISMEX Official", layout="wide")

# Handle Referrals from URL
if "ref" in st.query_params:
    st.session_state.url_ref = st.query_params["ref"].replace("+", " ").upper().strip()
current_ref = st.session_state.get("url_ref", "")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; }
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button {
        background-color: #1c1e26 !important; color: #ffffff !important;
        border: 2px solid #333 !important; border-radius: 8px !important;
        font-weight: bold !important; width: 100% !important;
    }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #00ff88; }
    .roi-text { color: #00ff88; font-weight: bold; float: right; font-size: 18px; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. ADMIN PANEL LOGIC
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_registry()
    for user, u_data in reg.items():
        pending = u_data.get('pending_actions', [])
        for idx, act in enumerate(list(pending)):
            with st.expander(f"{act['type']} - {user} - ₱{act.get('amount',0):,.2f}"):
                if act['type'] == "WITHDRAW":
                    st.warning(f"BANK: {act.get('bank')} | ACCT: {act.get('acct_num')} | NAME: {act.get('acct_name')}")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", key=f"a_{user}_{idx}"):
                    if act['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": datetime.now().isoformat()})
                    u_data.setdefault('history', []).append({"type": act['type'], "amount": act['amount'], "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"})
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()
                if c2.button("❌ REJECT", key=f"r_{user}_{idx}"):
                    if act['type'] == "WITHDRAW": u_data['wallet'] = u_data.get('wallet', 0.0) + act['amount']
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# 4. USER DASHBOARD (FULL RESTORE)
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    user_display = st.session_state.user.upper()

    st.write(f"Investor: **{user_display}**")
    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

    st.markdown(f'<div class="balance-box"><p style="color:#8c8f99;">WITHDRAWABLE</p><h1 style="color:#00ff88;">₱{wallet:,.2f}</h1></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if col3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    # --- ACTION FORMS ---
    if st.session_state.action_type == "DEP":
        with st.form("dep_form"):
            st.markdown("### 📥 DEPOSIT REQUEST")
            st.info("💳 **GCASH:** 09XXXXXXXX | **NAME:** T*** S*** T.")
            amt_d = st.number_input("Amount (Min: ₱500)", min_value=500.0)
            st.file_uploader("Browse Receipt", type=['jpg', 'jpeg', 'png'])
            if st.form_submit_button("SEND TO ADMIN"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "WITH":
        with st.form("with_form"):
            st.markdown("### 💸 WITHDRAWAL")
            amt_w = st.number_input("Amount", 0.0, max_value=wallet)
            bnk = st.text_input("Bank / Gcash")
            acc = st.text_input("Account Number")
            if st.form_submit_button("SUBMIT REQUEST"):
                if amt_w > 0:
                    data['wallet'] = wallet - amt_w
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "bank":bnk, "acct_num":acc})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "REIN":
        with st.form("rein_form"):
            st.markdown("### ♻️ REINVEST")
            amt_r = st.number_input("Reinvest Amount", 0.0, max_value=wallet)
            if st.form_submit_button("CONFIRM REINVEST"):
                if amt_r > 0:
                    data['wallet'] = wallet - amt_r
                    data.setdefault('inv', []).append({"amount": amt_r, "start_time": datetime.now().isoformat()})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    # --- INVESTMENTS & REFERRALS ---
    st.markdown("### 🤝 YOUR REFERRAL LINK")
    st.code(f"https://ismex-philippines.streamlit.app/?ref={user_display.replace(' ', '+')}")

    st.markdown("### 🚀 ACTIVE CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No active investments.")
    for idx, a in enumerate(reversed(active)):
        start = datetime.fromisoformat(a['start_time'])
        end = start + timedelta(days=7)
        elapsed = (datetime.now() - start).total_seconds()
        prog = min(1.0, elapsed / (7*86400))
        roi = a['amount'] * 1.20
        
        st.markdown(f"<div class='hist-card'><span class='roi-text'>ROI: ₱{roi:,.2f}</span>CAPITAL: ₱{a['amount']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(prog)
        if datetime.now() >= end:
            if st.button(f"📥 PULL OUT ₱{roi:,.2f}", key=f"po_{idx}"):
                data['wallet'] = wallet + roi
                active.pop(len(active)-1-idx)
                update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 HISTORY")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ {h.get('type')} - ₱{h.get('amount',0):,.2f} | {h.get('date')}")

# 5. LANDING PAGE
elif st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    u = st.text_input("FULL NAME").upper().strip()
    p = st.text_input("PIN", type="password")
    if st.button("LOGIN"):
        reg = load_registry()
        if u in reg and str(reg[u]['pin']) == str(p): st.session_state.user = u; st.rerun()
        else: st.error("Incorrect Name or PIN")
    if st.button("BACK"): st.session_state.page = "ad"; st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 GET STARTED / LOGIN", use_container_width=True): st.session_state.page = "login"; st.rerun()
    
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
