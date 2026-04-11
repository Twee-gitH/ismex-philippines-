import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. UI & SECURE SHIELD (PRESERVED)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2.5rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 25px;
    }
    .hist-card {
        background: #1c2128; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #00ff88;
    }
    .main .block-container { padding-bottom: 300px !important; }
    </style>
    """, unsafe_allow_html=True)

st.components.v1.html("""
    <script>
    const maintainShield = () => {
        const p = window.parent.document;
        let s = p.getElementById('ismex-master-shield');
        if (!s) {
            s = p.createElement('div');
            s.id = 'ismex-master-shield';
            s.style.cssText = 'position:fixed;bottom:0;left:0;width:100vw;height:130px;background:#0e1117;z-index:2147483647;pointer-events:none;';
            p.body.appendChild(s);
        }
        const b = p.querySelector('.viewerBadge_container__1QSob');
        if (b) b.style.display = 'none';
    };
    setInterval(maintainShield, 100);
    </script>
    """, height=0)

# ==========================================
# 2. DATABASE & STATE (PRESERVED)
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

def load_reg():
    return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}

def save(n, d):
    db.collection("investors").document(n).set(d)

for k, v in [('user',None), ('page','landing'), ('is_boss',False), ('action_type',None)]:
    if k not in st.session_state: st.session_state[k] = v

if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# 3. FULL ADMIN LOGIC (ADDED: MEMBER TABLE & PIN AUDIT)
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN COMMAND CENTER")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    t1, t2 = st.tabs(["📥 PENDING APPROVALS", "👥 MEMBER DATABASE & PINS"])
    
    with t1:
        for u, u_data in reg.items():
            pend = u_data.get('pending_actions', [])
            for idx, act in enumerate(list(pend)):
                with st.expander(f"REQ: {act['type']} - {u} (₱{act.get('amount',0):,.2f})"):
                    if 'details' in act: st.info(f"DETAILS: {act['details']}")
                    c1, c2 = st.columns(2)
                    if c1.button("APPROVE", key=f"ap_{u}_{idx}"):
                        ph_now = (datetime.now() + timedelta(hours=8))
                        amt = act['amount']
                        # 20% Referral Logic
                        if act['type'] == "DEPOSIT" and not u_data.get('has_deposited'):
                            inv = u_data.get('ref_by', 'OFFICIAL')
                            if inv in reg:
                                reg[inv]['wallet'] = reg[inv].get('wallet', 0) + (amt * 0.20)
                                save(inv, reg[inv])
                            u_data['has_deposited'] = True
                        if act['type'] in ["DEPOSIT", "REINVEST"]:
                            u_data.setdefault('inv', []).append({"amount": amt, "start_time": ph_now.isoformat()})
                        for h in u_data.get('history', []):
                            if h.get('request_id') == act.get('request_id'): h['status'] = "CONFIRMED"
                        u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()
                    if c2.button("REJECT", key=f"rj_{u}_{idx}"):
                        if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                        u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()

    with t2:
        st.subheader("📊 MASTER MEMBER TABLE")
        audit_list = []
        for name, info in reg.items():
            audit_list.append({
                "NAME": name, 
                "PIN": info.get('pin'), 
                "WALLET": f"₱{info.get('wallet',0):,.2f}", 
                "INVITED BY": info.get('ref_by', 'N/A')
            })
        st.table(audit_list)
        
        st.subheader("🔍 MEMBER HISTORY AUDIT")
        sel_user = st.selectbox("Select User to Audit History", list(reg.keys()))
        if sel_user:
            st.write(f"Showing Full History for: **{sel_user}**")
            st.json(reg[sel_user].get('history', []))

# ==========================================
# 4. USER DASHBOARD (ALL FORMS PRESERVED)
# ==========================================
elif st.session_state.user:
    reg = load_registry() if 'load_registry' in globals() else load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    req_id = ph_now.strftime("%f")

    st.title(f"ISMEX | {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>WALLET</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # --- WITHDRAW FORM (PRESERVED) ---
    if st.session_state.action_type == "WIT":
        with st.form("withdraw_form"):
            amt_w = st.number_input("Amount", 500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank Details (Name/Number)")
            if st.form_submit_button("SUBMIT"):
                if wallet >= amt_w:
                    data['wallet'] = wallet - amt_w
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "request_id":req_id, "details":bank})
                    data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt_w, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # --- REINVEST FORM (PRESERVED) ---
    if st.session_state.action_type == "REI":
        with st.form("reinvest_form"):
            amt_r = st.number_input("Reinvest Amount", 500.0, max_value=max(500.0, wallet))
            if st.form_submit_button("CONFIRM"):
                data['wallet'] = wallet - amt_r
                data.setdefault('pending_actions', []).append({"type":"REINVEST", "amount":amt_r, "request_id":req_id})
                data.setdefault('history', []).append({"type":"REINVEST", "amount":amt_r, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # --- DEPOSIT FORM (PRESERVED) ---
    if st.session_state.action_type == "DEP":
        with st.form("deposit_form"):
            amt_d = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("SEND"):
                data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt_d, "request_id":req_id})
                data.setdefault('history', []).append({"type":"DEPOSIT", "amount":amt_d, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # --- ADDED: USER REFERRAL TABLE ---
    st.markdown("---")
    st.subheader("👥 MY REFERRAL NETWORK (20%)")
    ref_slug = st.session_state.user.replace(' ', '+')
    st.code(f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={ref_slug}")
    
    ref_list = []
    for n, i in reg.items():
        if i.get('ref_by') == st.session_state.user:
            f_dep = i['inv'][0]['amount'] if (i.get('inv') and i.get('has_deposited')) else 0
            ref_list.append({"Name": n, "First Deposit": f"₱{f_dep:,.2f}", "Earned": f"₱{f_dep*0.20:,.2f}"})
    if ref_list: st.table(ref_list)
    else: st.info("No referrals yet.")

    # --- ROI & HISTORY (PRESERVED) ---
    st.markdown("### 📜 TRANSACTION HISTORY")
    for h in reversed(data.get('history', [])):
        color = "#00ff88" if h.get('status') == "CONFIRMED" else "#ffaa00"
        st.markdown(f"<div class='hist-card' style='border-left-color:{color}'><b>{h['type']}</b> | ₱{h['amount']:,.2f} | {h['status']}</div>", unsafe_allow_html=True)

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================
# 5. AUTH & ADMIN BUTTON (PRESERVED)
# ==========================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            r = load_reg()
            if u in r and str(r[u]['pin']) == p: st.session_state.user = u; st.rerun()
    with t2:
        inv = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"Invited by: {inv}")
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("PIN (6-Digit)", type="password", max_chars=6)
        if st.button("REGISTER"):
            save(nu, {"pin":np, "wallet":0.0, "ref_by":inv, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Registered!"); st.rerun()
else:
    st.title("ISMEX PHILIPPINES")
    if st.button("🚀 ENTER"): st.session_state.page = "auth"; st.rerun()
    
    # --- ADMIN ACCESS BUTTON (PRESERVED) ---
    st.markdown("---")
    with st.expander("🔒"):
        key = st.text_input("Key", type="password")
        if st.button("🔑"):
            if key == "0102030405": st.session_state.is_boss = True; st.rerun()
                
