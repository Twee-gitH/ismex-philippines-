import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & THE ANTI-BRANDING SHIELD
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    /* 1. HIDE NATIVE ELEMENTS */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu, 
    .viewerBadge_container__1QSob, .viewerBadge_link__1QSob,
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; 
        display: none !important; 
    }

    /* 2. THE TOP-LAYER SHIELD (THE "COVER") */
    /* This creates a physical black bar at the very bottom that sits ABOVE the Streamlit icon */
    .mobile-shield {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 50px;
        background-color: #0e1117; /* Matches your background color */
        z-index: 9999999; /* Higher than everything else */
        pointer-events: auto; /* Blocks clicks to the icons underneath */
    }

    /* 3. THEME COLORS */
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button { background-color: #1c1e26 !important; color: #ffffff !important; border: 2px solid #333 !important; border-radius: 8px !important; width: 100% !important; }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #00ff88; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 15px; }
    
    /* Extra padding so your buttons aren't covered by the shield */
    .main .block-container { padding-bottom: 100px !important; }
    </style>
    
    <div class="mobile-shield"></div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATABASE CONNECTION
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
    st.error(f"DATABASE ERROR: {e}")

def load_registry():
    try: return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State initialization
for key, val in [('page','landing'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

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
                if 'bank_details' in act: st.write(f"🏦 {act['bank_details']}")
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", key=f"a_{user}_{idx}"):
                    ph_now = datetime.now() + timedelta(hours=8)
                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": ph_now.isoformat()})
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'): h['status'] = "CONFIRMED"
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()
                if c2.button("❌ REJECT", key=f"r_{user}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet', 0.0) + act['amount']
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'): h['status'] = "REJECTED"
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = data.get('wallet', 0.0)
    
    ph_now = datetime.now() + timedelta(hours=8)
    now_str = ph_now.strftime("%Y-%m-%d %I:%M %p")
    req_id = ph_now.strftime("%f")

    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    if st.session_state.action_type == "DEP":
        with st.form("dep_f"):
            amt = st.number_input("Deposit Amount", min_value=500.0)
            receipt = st.file_uploader("Browse Receipt", type=['jpg', 'png', 'jpeg'])
            if st.form_submit_button("SEND TO ADMIN"):
                if receipt:
                    data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt, "request_id": req_id})
                    data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "date": now_str, "status": "PENDING", "request_id": req_id})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.warning("Please upload receipt first")
    
        if st.session_state.action_type == "WIT":
        with st.form("wit_f"):
            # Ensure max_value is at least 500.0 to prevent the crash
            safe_max = max(500.0, float(wallet))
            
            amt = st.number_input("Withdraw Amount", min_value=500.0, max_value=safe_max)
            bank = st.text_input("Bank Name").upper()
            acc_name = st.text_input("Account Name").upper()
            acc_num = st.text_input("Account Number")
            if st.form_submit_button("REQUEST WITHDRAW"):
                if wallet < amt:
                    st.error("Insufficient Balance!")
                elif bank and acc_name and acc_num:
                    data['wallet'] -= amt
                    details = f"{bank} | {acc_name} | {acc_num}"
                    data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt, "request_id": req_id, "bank_details": details})
                    data.setdefault('history', []).append({"type": "WITHDRAW", "amount": amt, "date": now_str, "status": "PENDING", "request_id": req_id})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.error("Fill all bank details!")
                    

        if st.session_state.action_type == "REI":
        with st.form("rei_f"):
            # Ensure max_value is at least 500.0 to prevent the crash
            safe_max_rei = max(500.0, float(wallet))
            
            amt = st.number_input("Reinvest Amount (Minimum ₱500)", min_value=500.0, max_value=safe_max_rei)
            if st.form_submit_button("CONFIRM REINVEST"):
                if wallet < amt:
                    st.error("Insufficient Balance!")
                else:
                    data['wallet'] -= amt
                    data.setdefault('pending_actions', []).append({"type": "REINVEST", "amount": amt, "request_id": req_id})
                    data.setdefault('history', []).append({"type": "REINVEST", "amount": amt, "date": now_str, "status": "PENDING", "request_id": req_id})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                    

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

    st.markdown("---")
    st.subheader("👥 REFERRAL INFO")
    u_ref = st.session_state.user.replace(' ', '+')
    ref_url = f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={u_ref}"
    st.code(ref_url)
    ref_list, total_c = [], 0
    for n, i in reg.items():
        if i.get('ref_by') == st.session_state.user:
            f_dep = i['inv'][0]['amount'] if i.get('inv') else 0
            comm = f_dep * 0.30
            total_c += comm
            ref_list.append({"Name": n, "1st Deposit": f"₱{f_dep:,.2f}", "Comm": f"₱{comm:,.2f}"})
    if ref_list:
        st.table(ref_list)
        if st.button("💸 REQUEST COMMISSION WITHDRAW"):
            data.setdefault('pending_actions', []).append({"type": "COMM_WITHDRAW", "amount": total_c, "request_id": req_id})
            data.setdefault('history', []).append({"type": "COMM_WITHDRAW", "amount": total_c, "date": now_str, "status": "PENDING", "request_id": req_id})
            update_user(st.session_state.user, data); st.rerun()

    st.markdown("---")
    st.markdown("### 🚀 ACTIVE CAPITALS")
    active = data.get('inv', [])
    for idx, a in enumerate(reversed(active)):
        start = datetime.fromisoformat(a['start_time'])
        end = start + timedelta(days=7)
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        roi = a['amount'] * 1.20
        st.markdown(f"<div class='hist-card'><span style='color:#00ff88; float:right;'>ROI: ₱{roi:,.2f}</span>CAPITAL: ₱{a['amount']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(prog)
        if ph_now >= end:
            if st.button(f"📥 PULL OUT ₱{roi:,.2f}", key=f"po_{idx}"):
                data['wallet'] = wallet + roi
                data.setdefault('history', []).append({"type": "PULL OUT", "amount": roi, "date": now_str, "status": "CONFIRMED"})
                active.pop(len(active)-1-idx)
                update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 HISTORY")
    for h in reversed(data.get('history', [])):
        c = "#ffaa00" if h.get('status') == "PENDING" else "#00ff88"
        st.markdown(f"**{h.get('type')}** | ₱{h.get('amount',0):,.2f} | {h.get('date')} | <span style='color:{c}'>{h.get('status')}</span>", unsafe_allow_html=True)

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
                st.success("Success!")
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

# This part ensures the branding is hidden by forcing it at the bottom-most level
st.components.v1.html("""
    <script>
    const hideElements = () => {
        const elements = window.parent.document.querySelectorAll('footer, .stDeployButton, header');
        elements.forEach(el => el.style.display = 'none');
    };
    setInterval(hideElements, 100);
    </script>
    """, height=0)
                
