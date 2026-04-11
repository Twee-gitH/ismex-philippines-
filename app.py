import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & THE PHYSICAL WALL (UI)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"] { visibility: hidden !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .hist-card {
        background: #1c2128; padding: 18px; border-radius: 12px;
        margin-bottom: 12px; border-left: 6px solid #00ff88;
    }
    .main .block-container { padding-bottom: 250px !important; }
    </style>
    """, unsafe_allow_html=True)

# THE GITHUB INJECTION: Preserving your specific wall logic
st.components.v1.html("""
    <script>
    const buryBranding = () => {
        const topDoc = window.parent.document;
        let wall = topDoc.getElementById('ismex-final-shield');
        if (!wall) {
            wall = topDoc.createElement('div');
            wall.id = 'ismex-final-shield';
            wall.style.cssText = `
                position: fixed !important; bottom: 0 !important; left: 0 !important;
                width: 100vw !important; height: 125px !important;
                background: #0e1117 !important; z-index: 2147483647 !important;
                display: block !important; border-top: 2px solid #0e1117;
                pointer-events: none !important;
            `;
            topDoc.body.appendChild(wall);
        }
        const badge = topDoc.querySelector('.viewerBadge_container__1QSob');
        const footer = topDoc.querySelector('footer');
        if (badge) badge.style.display = 'none';
        if (footer) footer.style.display = 'none';
    };
    setInterval(buryBranding, 100);
    </script>
    """, height=0)

# ==========================================
# 2. DATABASE CONNECTION (LOGIC)
# ==========================================
@st.cache_resource
def get_db():
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
            return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"DATABASE ERROR: {e}")
    return None

db = get_db()

def load_registry():
    try: return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# Init State
for key, val in [('page','landing'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# 3. ADMIN PANEL (PRESERVED Logic)
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
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = float(u_data.get('wallet', 0.0)) + act['amount']
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'): h['status'] = "REJECTED"
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD (FULL RESTORE)
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    now_str = ph_now.strftime("%Y-%m-%d %I:%M %p")
    req_id = ph_now.strftime("%f")

    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div style='background:linear-gradient(135deg,#1e222d,#0e1117);padding:2rem;border-radius:20px;border:2px solid #00ff88;text-align:center;'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # RESTORED: Receipt Uploader Logic
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
    
    # RESTORED: Withdraw Logic
    if st.session_state.action_type == "WIT":
        with st.form("wit_f"):
            amt = st.number_input("Withdraw Amount", min_value=500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank Details").upper()
            if st.form_submit_button("REQUEST WITHDRAW"):
                if wallet >= amt and bank:
                    data['wallet'] = wallet - amt
                    data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt, "request_id": req_id, "bank_details": bank})
                    data.setdefault('history', []).append({"type": "WITHDRAW", "amount": amt, "date": now_str, "status": "PENDING", "request_id": req_id})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    # RESTORED: Referral & ROI Logics
    st.markdown("---")
    st.subheader("👥 REFERRAL INFO")
    u_ref = st.session_state.user.replace(' ', '+')
    st.code(f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={u_ref}")
    
    # ROI Logic (FIXED KEY ERROR)
    st.subheader("🚀 ACTIVE CAPITALS")
    active = data.get('inv', [])
    for idx, a in enumerate(list(active)):
        # Checks both possible keys to prevent crash
        raw_start = a.get('start_time') or a.get('date')
        if raw_start:
            start = datetime.fromisoformat(raw_start)
            end = start + timedelta(days=7)
            prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
            roi = a['amount'] * 1.20
            st.markdown(f"<div class='hist-card'><span style='color:#00ff88; float:right;'>ROI: ₱{roi:,.2f}</span>CAPITAL: ₱{a['amount']:,.2f}</div>", unsafe_allow_html=True)
            st.progress(prog)
            if ph_now >= end and st.button(f"📥 PULL OUT ₱{roi:,.2f}", key=f"po_{idx}"):
                data['wallet'] = wallet + roi
                active.pop(idx)
                update_user(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

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
            if u_log in reg and str(reg[u_log].get('pin')) == str(p_log):
                st.session_state.user = u_log; st.rerun()
    with tab2:
        inviter = st.session_state.get('captured_ref', 'OFFICIAL')
        new_u = st.text_input("YOUR FULL NAME").upper().strip()
        new_p = st.text_input("SET PIN", type="password", max_chars=4)
        if st.button("CREATE ACCOUNT"):
            update_user(new_u, {"pin": new_p, "wallet": 0.0, "ref_by": inviter, "inv": [], "history": [], "pending_actions": []})
            st.success("Success!")
    if st.button("← BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 GET STARTED"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Key", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                    
