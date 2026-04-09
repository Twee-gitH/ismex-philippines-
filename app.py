import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import json

# ==========================================
# 1. DATABASE CONNECTION
# ==========================================
try:
    if "firebase" in st.secrets:
        raw_key = st.secrets["firebase"]["private_key"]
        fixed_key = raw_key.replace("\\n", "\n")
        creds_dict = {
            "type": st.secrets["firebase"]["type"], "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"], "private_key": fixed_key,
            "client_email": st.secrets["firebase"]["client_email"], "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"], "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=creds)
except Exception as e:
    st.error(f"DATABASE CRASH: {e}")

def load_registry():
    try: return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State initialization
for key, val in [('page','landing'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. UI STYLES (THE INVISIBLE WRAPPER)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button { background-color: #1c1e26 !important; color: #ffffff !important; border: 2px solid #333 !important; border-radius: 8px !important; width: 100% !important; }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #00ff88; }
    .roi-text { color: #00ff88; font-weight: bold; float: right; font-size: 18px; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# 3. ADMIN PANEL
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    reg = load_registry()
    for user, u_data in reg.items():
        pending = u_data.get('pending_actions', [])
        for idx, act in enumerate(list(pending)):
            with st.expander(f"{act['type']} - {user} - ₱{act.get('amount',0):,.2f}"):
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", key=f"a_{user}_{idx}"):
                    if act['type'] == "DEPOSIT" or act['type'] == "REINVEST":
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": datetime.now().isoformat()})
                    elif act['type'] == "WITHDRAW":
                        pass # Funds already deducted from wallet during request
                    elif act['type'] == "COMM_WITHDRAW":
                        pass
                    u_data.setdefault('history', []).append({"type": act['type'], "amount": act['amount'], "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"})
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()
                if c2.button("❌ REJECT", key=f"r_{user}_{idx}"):
                    if act['type'] == "WITHDRAW" or act['type'] == "REINVEST":
                        u_data['wallet'] = u_data.get('wallet', 0.0) + act['amount']
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = data.get('wallet', 0.0)

    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    # --- TRANSACTION BUTTONS ---
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # Transaction Forms
    if st.session_state.action_type == "DEP":
        with st.form("dep_f"):
            amt = st.number_input("Deposit Amount", min_value=500.0)
            st.file_uploader("Upload Receipt")
            if st.form_submit_button("SEND TO ADMIN"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
    
    if st.session_state.action_type == "WIT":
        with st.form("wit_f"):
            amt = st.number_input("Withdraw Amount", min_value=500.0, max_value=wallet)
            if st.form_submit_button("REQUEST WITHDRAW"):
                data['wallet'] -= amt
                data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.session_state.action_type == "REI":
        with st.form("rei_f"):
            amt = st.number_input("Reinvest Amount", min_value=500.0, max_value=wallet)
            if st.form_submit_button("CONFIRM REINVEST"):
                data['wallet'] -= amt
                data.setdefault('pending_actions', []).append({"type": "REINVEST", "amount": amt})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

    # --- REFERRAL INFO ---
    st.markdown("---")
    st.subheader("👥 REFERRAL INFO (30%)")
    ref_link = f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={st.session_state.user.replace(' ', '+')}"
    st.code(ref_link)
    ref_list = []
    total_c = 0
    for n, i in reg.items():
        if i.get('ref_by') == st.session_state.user:
            f_dep = i['inv'][0]['amount'] if i.get('inv') else 0
            comm = f_dep * 0.30
            total_c += comm
            ref_list.append({"Name": n, "1st Deposit": f"₱{f_dep:,.2f}", "Comm": f"₱{comm:,.2f}"})
    if ref_list:
        st.table(ref_list)
        if st.button("💸 REQUEST COMMISSION WITHDRAW"):
            data.setdefault('pending_actions', []).append({"type": "COMM_WITHDRAW", "amount": total_c})
            update_user(st.session_state.user, data); st.success("Requested!"); st.rerun()

    # --- ACTIVE CAPITALS ---
    st.markdown("---")
    st.markdown("### 🚀 ACTIVE CAPITALS")
    active = data.get('inv', [])
    for idx, a in enumerate(reversed(active)):
        start = datetime.fromisoformat(a['start_time'])
        end = start + timedelta(days=7)
        prog = min(1.0, (datetime.now() - start).total_seconds() / (7*86400))
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

# ==========================================
# 5. LANDING & AUTH
# ==========================================
elif st.session_state.page == "auth":
    tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
    with tab1:
        u_log = st.text_input("FULL NAME").upper().strip()
        p_log = st.text_input("PIN", type="password")
        if st.button("ENTER ISMEX"):
            reg = load_registry()
            if u_log in reg and str(reg[u_log]['pin']) == str(p_log):
                st.session_state.user = u_log; st.rerun()
            else: st.error("Invalid Credentials")
    with tab2:
        inviter = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"🤝 Invited by: {inviter}")
        new_u = st.text_input("YOUR FULL NAME").upper().strip()
        new_p = st.text_input("SET PIN", type="password", max_chars=4)
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if new_u in reg: st.error("NAME ALREADY REGISTERED!")
            else:
                update_user(new_u, {"pin": new_p, "wallet": 0.0, "ref_by": inviter, "inv": [], "history": [], "pending_actions": []})
                st.success("Registration Successful!")
    if st.button("← BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 PRESS HERE TO REGISTER OR LOG IN", use_container_width=True):
        st.session_state.page = "auth"; st.rerun()
    col_a, _ = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
    
