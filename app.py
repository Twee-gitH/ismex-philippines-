import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. UI & THE GITHUB SHIELD
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
    const shield = () => {
        const p = window.parent.document;
        let s = p.getElementById('ismex-shield');
        if (!s) {
            s = p.createElement('div');
            s.id = 'ismex-shield';
            s.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;height:130px;background:#0e1117;z-index:2147483647;pointer-events:none;';
            p.body.appendChild(s);
        }
        const b = p.querySelector('.viewerBadge_container__1QSob');
        if (b) b.style.display = 'none';
    };
    setInterval(shield, 100);
    </script>
    """, height=0)

# ==========================================
# 2. DATABASE CONNECTIVITY
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
# 3. ADMIN PANEL: REACTION LOGIC (20% REF)
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, u_data in reg.items():
        pend = u_data.get('pending_actions', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"REQ: {act['type']} - {u} (₱{act.get('amount',0):,.2f})"):
                if 'details' in act: st.info(f"BANK DETAILS: {act['details']}")
                
                c1, c2 = st.columns(2)
                if c1.button("APPROVE", key=f"app_{u}_{idx}"):
                    ph_now = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %I:%M %p")
                    amt = act['amount']
                    
                    # 20% Referral Commission Reaction
                    if act['type'] == "DEPOSIT" and not u_data.get('has_deposited', False):
                        inviter = u_data.get('ref_by', 'OFFICIAL')
                        if inviter in reg:
                            comm = amt * 0.20
                            reg[inviter]['wallet'] = reg[inviter].get('wallet', 0) + comm
                            reg[inviter].setdefault('history', []).append({
                                "type": "REFERRAL BONUS", "amount": comm, "date": ph_now, 
                                "status": "RECEIVED", "note": f"20% from {u}"
                            })
                            save(inviter, reg[inviter])
                        u_data['has_deposited'] = True

                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": amt, "start_time": datetime.now().isoformat()})
                    
                    # Log Reaction in History
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'):
                            h['status'] = "CONFIRMED"
                            h['admin_reaction'] = f"Approved at {ph_now}"
                    
                    u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("REJECT", key=f"rej_{u}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                    u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD: FULL LOGIC & AUDIT TRAIL
# ==========================================
elif st.session_state.user:
    reg = load_reg(); data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    now_str = ph_now.strftime("%Y-%m-%d %I:%M %p")
    req_id = ph_now.strftime("%f")

    st.title(f"ISMEX | {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # FULL WITHDRAW LOGIC
    if st.session_state.action_type == "WIT":
        with st.form("wit_form"):
            amt_w = st.number_input("Withdraw Amount", min_value=500.0, max_value=max(500.0, wallet))
            bank_info = st.text_input("Bank / GCash Details (Account Name & Number)")
            if st.form_submit_button("SUBMIT WITHDRAWAL"):
                if wallet >= amt_w and bank_info:
                    data['wallet'] = wallet - amt_w
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "request_id":req_id, "details":bank_info})
                    data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt_w, "status":"PENDING", "request_id":req_id, "date":now_str})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # FULL REINVEST LOGIC
    if st.session_state.action_type == "REI":
        with st.form("rei_form"):
            amt_r = st.number_input("Reinvest Amount", min_value=500.0, max_value=max(500.0, wallet))
            if st.form_submit_button("CONFIRM REINVESTMENT"):
                if wallet >= amt_r:
                    data['wallet'] = wallet - amt_r
                    data.setdefault('pending_actions', []).append({"type":"REINVEST", "amount":amt_r, "request_id":req_id})
                    data.setdefault('history', []).append({"type":"REINVEST", "amount":amt_r, "status":"PENDING", "request_id":req_id, "date":now_str})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # DEPOSIT LOGIC + RECEIPT UPLOADER
    if st.session_state.action_type == "DEP":
        with st.form("dep_form"):
            amt_d = st.number_input("Deposit Amount", 500.0)
            receipt = st.file_uploader("Upload Receipt Image", type=['jpg','png','jpeg'])
            if st.form_submit_button("SEND TO ADMIN"):
                if receipt:
                    data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt_d, "request_id":req_id})
                    data.setdefault('history', []).append({"type":"DEPOSIT", "amount":amt_d, "status":"PENDING", "request_id":req_id, "date":now_str})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # ACTIVE INVESTMENTS (20% WEEKLY)
    st.markdown("---")
    st.subheader("🚀 ACTIVE CAPITALS")
    for idx, i in enumerate(list(data.get('inv', []))):
        start = datetime.fromisoformat(i.get('start_time') or i.get('date'))
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        roi = i['amount'] * 1.20
        st.write(f"₱{i['amount']:,} -> ₱{roi:,.2f}"); st.progress(prog)
        if ph_now >= start + timedelta(days=7) and st.button(f"CLAIM ₱{roi:,.2f}", key=f"c_{idx}"):
            data['wallet'] = wallet + roi; data['inv'].pop(idx); save(st.session_state.user, data); st.rerun()

    # AUDIT TRAIL HISTORY VISIBILITY
    st.markdown("---")
    st.subheader("📜 FULL TRANSACTION HISTORY")
    u_hist = data.get('history', [])
    if u_hist:
        for h in reversed(u_hist):
            st.markdown(f"""
                <div class='hist-card'>
                    <b>{h.get('type')}</b> | ₱{h.get('amount', 0):,.2f}<br>
                    <small>{h.get('date')}</small> | <b>{h.get('status')}</b><br>
                    <span style='font-size:0.8rem; color:#888;'>{h.get('admin_reaction', 'Pending Verification')}</span>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("No transaction history.")

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================
# 5. AUTH & LANDING
# ==========================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u_in = st.text_input("NAME").upper().strip()
        p_in = st.text_input("PIN", type="password")
        if st.button("GO"):
            r = load_reg()
            if u_in in r and str(r[u_in].get('pin')) == p_in: st.session_state.user = u_in; st.rerun()
    with t2:
        inv = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"Invited by: {inv}")
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("PIN", type="password", max_chars=4)
        if st.button("JOIN"):
            save(nu, {"pin":np, "wallet":0.0, "ref_by":inv, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 ENTER"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Key", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
    
