import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# ZONE 1: UI & PHYSICAL WALL
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"] { visibility: hidden !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d, #0e1117);
        padding: 2rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 25px;
    }
    .hist-card {
        background: #1c2128; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #00ff88;
    }
    .main .block-container { padding-bottom: 250px !important; }
    </style>
    """, unsafe_allow_html=True)

# The Wall (JavaScript)
st.components.v1.html("""
    <script>
    const bury = () => {
        const top = window.parent.document;
        let wall = top.getElementById('ismex-shield');
        if (!wall) {
            wall = top.createElement('div');
            wall.id = 'ismex-shield';
            wall.style.cssText = 'position:fixed;bottom:0;left:0;width:100vw;height:125px;background:#0e1117;z-index:2147483647;pointer-events:none;';
            top.body.appendChild(wall);
        }
        const b = top.querySelector('.viewerBadge_container__1QSob');
        if (b) b.style.display = 'none';
    };
    setInterval(bury, 100);
    </script>
    """, height=0)

# ==========================================
# ZONE 2: DB CONNECTIVITY
# ==========================================
@st.cache_resource
def get_db():
    if "firebase" in st.secrets:
        info = dict(st.secrets["firebase"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds)
    return None

db = get_db()

def load_registry():
    return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State
for k, v in [('page','landing'), ('user',None), ('is_boss',False), ('action_type',None)]:
    if k not in st.session_state: st.session_state[k] = v

# POINT 1: URL Detection Logic
if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# ZONE 3: ADMIN PANEL (POINT 2 & 4: Commission Logic)
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
                    ph_now = (datetime.now() + timedelta(hours=8)).isoformat()
                    amt = act['amount']
                    
                    # POINT 2 & 4: THE "FIRST DEPOSIT ONLY" 30% RULE
                    if act['type'] == "DEPOSIT" and not u_data.get('has_deposited', False):
                        inviter_name = u_data.get('ref_by', 'OFFICIAL')
                        if inviter_name in reg:
                            comm_amt = amt * 0.30
                            inviter_data = reg[inviter_name]
                            inviter_data['wallet'] = inviter_data.get('wallet', 0) + comm_amt
                            update_user(inviter_name, inviter_data)
                            st.toast(f"💰 Sent ₱{comm_amt:,.2f} commission to {inviter_name}")
                        u_data['has_deposited'] = True  # The Lock

                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": amt, "start_time": ph_now})
                    
                    # Update History status
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'): h['status'] = "CONFIRMED"
                    
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()
                
                if c2.button("❌ REJECT", key=f"r_{user}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# ==========================================
# ZONE 4: USER DASHBOARD (POINT 3: Referral Table)
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    # Forms (Deposit, Withdraw, Reinvest)
    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if c3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            amt = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Browse Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("SUBMIT"):
                if receipt:
                    rid = ph_now.strftime("%f")
                    data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt, "request_id":rid})
                    data.setdefault('history', []).append({"type":"DEPOSIT", "amount":amt, "status":"PENDING", "request_id":rid, "date":ph_now.strftime("%Y-%m-%d")})
                    update_user(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # POINT 3: THE REFERRAL TABLE
    st.markdown("---")
    st.subheader("👥 MY REFERRAL NETWORK")
    ref_list = []
    for name, u_data in reg.items():
        if u_data.get('ref_by') == st.session_state.user:
            first_dep = u_data['inv'][0]['amount'] if (u_data.get('inv') and u_data.get('has_deposited')) else 0
            comm = first_dep * 0.30
            status = "PAID" if u_data.get('has_deposited') else "PENDING"
            ref_list.append({"Invited Name": name, "First Deposit": f"₱{first_dep:,.2f}", "My Comm": f"₱{comm:,.2f}", "Status": status})
    if ref_list: st.table(ref_list)
    else: st.info("No referrals yet.")

    # ROI Logic (20% Weekly)
    st.markdown("---")
    st.subheader("🚀 ACTIVE CAPITALS (20% WEEKLY)")
    invs = data.get('inv', [])
    for idx, i in enumerate(list(invs)):
        start = datetime.fromisoformat(i['start_time'])
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        roi = i['amount'] * 1.20
        st.write(f"₱{i['amount']:,} -> ₱{roi:,.2f}")
        st.progress(prog)
        if ph_now >= start + timedelta(days=7):
            if st.button(f"CLAIM ₱{roi:,.2f}", key=f"c_{idx}"):
                data['wallet'] = wallet + roi
                data['inv'].pop(idx); update_user(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================
# ZONE 5: AUTHENTICATION
# ==========================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("FULL NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            r = load_registry()
            if u in r and str(r[u].get('pin')) == p:
                st.session_state.user = u; st.rerun()
    with t2:
        # POINT 1: Auto-Fill the Inviter from URL
        inviter = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"Invited by: {inviter}")
        nu = st.text_input("NEW FULL NAME").upper().strip()
        np = st.text_input("SET 4-DIGIT PIN", type="password", max_chars=4)
        if st.button("REGISTER"):
            update_user(nu, {"pin":np, "wallet":0.0, "ref_by":inviter, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("GET STARTED"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Admin", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                            
