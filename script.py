import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. DATABASE CONNECTION
# ==========================================
try:
    if "firebase" in st.secrets:
        creds_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=creds)
except Exception as e:
    st.error(f"Setup Error: {e}")

def load_registry():
    try:
        return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State initialization
for key, val in [('page','ad'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. UI STYLES
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    header, footer, .stDeployButton {visibility: hidden !important;}
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button {
        background-color: #1c1e26 !important; color: #ffffff !important;
        border: 2px solid #333 !important; border-radius: 8px !important;
        font-weight: bold !important; width: 100% !important;
    }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #00ff88; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. ADMIN PANEL
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    reg = load_registry()
    for user, u_data in reg.items():
        for idx, act in enumerate(list(u_data.get('pending_actions', []))):
            with st.expander(f"{act['type']} - {user}"):
                if st.button("✅ APPROVE", key=f"ap_{user}_{idx}"):
                    if act['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": datetime.now().isoformat()})
                    u_data.setdefault('history', []).append({"type": act['type'], "amount": act['amount'], "date": datetime.now().strftime("%Y-%m-%d"), "status": "CONFIRMED"})
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    st.write(f"Logged in: **{st.session_state.user.upper()}**")
    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

    st.markdown(f'<div class="balance-box"><h1>₱{wallet:,.2f}</h1></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            amt = st.number_input("Amount", 500.0)
            st.file_uploader("Browse Receipt", type=['jpg','png'])
            if st.form_submit_button("SEND TO ADMIN"):
                data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "WITH":
        with st.form("w"):
            amt_w = st.number_input("Amount", 0.0, max_value=wallet)
            bnk = st.text_input("Bank Details")
            if st.form_submit_button("SUBMIT"):
                data['wallet'] = wallet - amt_w
                data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "details":bnk})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    st.markdown("### 🤝 REFERRAL LINK")
    st.code(f"https://ismex-philippines.streamlit.app/?ref={st.session_state.user.replace(' ', '+')}")

    st.markdown("### 🚀 ACTIVE INVESTMENTS")
    active = data.get('inv', [])
    for idx, a in enumerate(reversed(active)):
        start = datetime.fromisoformat(a['start_time'])
        end = start + timedelta(days=7)
        prog = min(1.0, (datetime.now() - start).total_seconds() / (7*86400))
        st.markdown(f"<div class='hist-card'>CAPITAL: ₱{a['amount']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(prog)
        if datetime.now() >= end:
            if st.button(f"PULL OUT ₱{a['amount']*1.2:,.2f}", key=f"po_{idx}"):
                data['wallet'] = wallet + (a['amount']*1.2)
                active.pop(len(active)-1-idx)
                update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 HISTORY")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ {h['type']} - ₱{h['amount']:,.2f} ({h['date']})")

# ==========================================
# 5. LANDING
# ==========================================
elif st.session_state.page == "login":
    u = st.text_input("NAME").upper().strip()
    p = st.text_input("PIN", type="password")
    if st.button("ENTER"):
        reg = load_registry()
        if u in reg and str(reg[u]['pin']) == str(p): st.session_state.user = u; st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 LOGIN"): st.session_state.page = "login"; st.rerun()
    if st.button("⛔"):
        if st.text_input("Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
                
