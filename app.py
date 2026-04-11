import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. UI & THE GITHUB FRONT-PAGE SHIELD
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
        box-shadow: 0 10px 30px rgba(0,255,136,0.1);
    }
    .hist-card {
        background: #1c2128; padding: 18px; border-radius: 12px;
        margin-bottom: 12px; border-left: 6px solid #00ff88;
    }
    .main .block-container { padding-bottom: 300px !important; }
    </style>
    """, unsafe_allow_html=True)

st.components.v1.html("""
    <script>
    const maintainWall = () => {
        const top = window.parent.document;
        let wall = top.getElementById('ismex-master-shield');
        if (!wall) {
            wall = top.createElement('div');
            wall.id = 'ismex-master-shield';
            wall.style.cssText = 'position:fixed!important;bottom:0!important;left:0!important;width:100vw!important;height:130px!important;background:#0e1117!important;z-index:2147483647!important;pointer-events:none!important;';
            top.body.appendChild(wall);
        }
        const badge = top.querySelector('.viewerBadge_container__1QSob');
        if (badge) { badge.style.display = 'none'; badge.style.opacity = '0'; }
    };
    setInterval(maintainWall, 100);
    </script>
    """, height=0)

# ==========================================
# 2. DATABASE & SESSION STATE
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
# 3. ADMIN PANEL: 20% COMMISSION REACTION
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, u_data in reg.items():
        pend = u_data.get('pending_actions', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"🔴 {act['type']} - {u} (₱{act.get('amount',0):,.2f})"):
                if 'details' in act: st.code(act['details'])
                c1, c2 = st.columns(2)
                
                if c1.button("APPROVE", key=f"app_{u}_{idx}"):
                    ph_now = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %I:%M %p")
                    amt = act['amount']
                    
                    # 20% Referral Reaction (Only First Deposit)
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
                    
                    for h in u_data.get('history', []):
                        if h.get('request_id') == act.get('request_id'):
                            h['status'] = "CONFIRMED"
                            h['admin_reaction'] = f"Approved {ph_now}"
                    
                    u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("REJECT", key=f"rej_{u}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                    u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()

# ==========================================
# 4. USER DASHBOARD: ALL LOGICS PRESERVED
# ==========================================
elif st.session_state.user:
    reg = load_reg(); data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    req_id = ph_now.strftime("%f")

    st.title(f"ISMEX | {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if c3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # RESTORED: Withdraw Logic
    if st.session_state.action_type == "WIT":
        with st.form("w"):
            amt = st.number_input("Amount", 500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank/GCash Info")
            if st.form_submit_button("REQUEST WITHDRAW"):
                if wallet >= amt:
                    data['wallet'] = wallet - amt
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt, "request_id":req_id, "details":bank})
                    data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # RESTORED: Reinvest Logic
    if st.session_state.action_type == "REI":
        with st.form("r"):
            amt = st.number_input("Reinvest", 500.0, max_value=max(500.0, wallet))
            if st.form_submit_button("CONFIRM"):
                data['wallet'] = wallet - amt
                data.setdefault('pending_actions', []).append({"type":"REINVEST", "amount":amt, "request_id":req_id})
                data.setdefault('history', []).append({"type":"REINVEST", "amount":amt, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # RESTORED: Deposit + Receipt Uploader
    if st.session_state.action_type == "DEP":
        with st.form("d"):
            amt = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("SUBMIT"):
                if receipt:
                    data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt, "request_id":req_id})
                    data.setdefault('history', []).append({"type":"DEPOSIT", "amount":amt, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # ROI Logic
    st.subheader("🚀 ACTIVE CAPITALS")
    for idx, i in enumerate(list(data.get('inv', []))):
        start = datetime.fromisoformat(i.get('start_time') or i.get('date'))
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        roi = i['amount'] * 1.20
        st.write(f"₱{i['amount']:,} -> ₱{roi:,.2f}"); st.progress(prog)
        if ph_now >= start + timedelta(days=7) and st.button(f"CLAIM ₱{roi:,.2f}", key=f"c_{idx}"):
            data['wallet'] = wallet + roi; data['inv'].pop(idx); save(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 HISTORY")
    for h in reversed(data.get('history', [])):
        color = "#00ff88" if h.get('status') in ["CONFIRMED", "RECEIVED"] else "#ffaa00"
        st.markdown(f"<div class='hist-card' style='border-left-color:{color};'><b>{h.get('type')}</b> | ₱{h.get('amount'):,.2f} | {h.get('status')}</div>", unsafe_allow_html=True)

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================
# 5. AUTHENTICATION & AUTO-URL LOGIC
# ==========================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("GO"):
            r = load_reg()
            if u in r and str(r[u].get('pin')) == p: st.session_state.user = u; st.rerun()
    with t2:
        inviter = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"🤝 Invited by: {inviter}")
        nu = st.text_input("NEW FULL NAME").upper().strip()
        np = st.text_input("SET PIN", type="password", max_chars=4)
        if st.button("JOIN"):
            save(nu, {"pin":np, "wallet":0.0, "ref_by":inviter, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 ENTER"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Key", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
    
