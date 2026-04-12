import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import time

# ==========================================
# 1. UI CONFIGURATION
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 20px;
    }
    .cap-card {
        background: #1c2128; padding: 20px; border-radius: 15px;
        margin-bottom: 15px; border: 1px solid #30363d;
    }
    .hist-card {
        background: #1c2128; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #00ff88;
    }
    .main .block-container { padding: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & STATE
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

if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'action_type' not in st.session_state: st.session_state.action_type = None

if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# 3. ADMIN ACCESS & APPROVAL LOGIC
# ==========================================
if st.session_state.page == "boss_key":
    st.title("🛡️ VERIFICATION")
    boss_pass = st.text_input("Key", type="password")
    if st.button("💃"):
        if boss_pass == "0102030405":
            st.session_state.is_boss = True
            st.session_state.page = "admin"
            st.rerun()
    if st.button("CANCEL"): 
        st.session_state.page = "landing"
        st.rerun()

if st.session_state.is_boss:
    st.title("👑 ADMIN")
    if st.button("EXIT"): 
        st.session_state.is_boss = False
        st.session_state.page = "landing"
        st.rerun()
    
    reg = load_reg()
    t1, t2 = st.tabs(["📥 APPROVALS", "👥 MEMBERS"])
    
    with t1:
        for u, u_data in reg.items():
            pend = u_data.get('pending_actions', [])
            for idx, act in enumerate(list(pend)):
                with st.expander(f"{act['type']} - {u} (₱{act.get('amount',0):,.2f})"):
                    c1, c2 = st.columns(2)
                    if c1.button("APPROVE", key=f"ap_{u}_{idx}"):
                        ph = datetime.now() + timedelta(hours=8)
                        if act['type'] == "DEPOSIT" and not u_data.get('has_deposited'):
                            inv = u_data.get('ref_by', 'OFFICIAL')
                            if inv in reg:
                                reg[inv]['wallet'] = reg[inv].get('wallet', 0) + (act['amount'] * 0.20)
                                save(inv, reg[inv])
                            u_data['has_deposited'] = True
                        if act['type'] in ["DEPOSIT", "REINVEST"]:
                            u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": ph.isoformat()})
                        for h in u_data.get('history', []):
                            if h.get('request_id') == act.get('request_id'): h['status'] = "CONFIRMED"
                        u_data['pending_actions'].pop(idx)
                        save(u, u_data)
                        st.rerun()
                    if c2.button("REJECT", key=f"rj_{u}_{idx}"):
                        if act['type'] in ["WITHDRAW", "REINVEST"]: 
                            u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                        u_data['pending_actions'].pop(idx)
                        save(u, u_data)
                        st.rerun()
    with t2:
        st.table([{"NAME": n, "PIN": i.get('pin'), "WALLET": i.get('wallet'), "REF": i.get('ref_by')} for n, i in reg.items()])

# ==========================================
# 4. USER DASHBOARD & TRANSACTION LOGIC
# ==========================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    req_id = ph_now.strftime("%f")

    st.markdown(f"<div class='balance-box'><h3>BALANCE</h3><h1>₱{max(0.0, wallet):,.2f}</h1></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT CAPITAL"): st.session_state.action_type = "DEPOSIT CAPITAL"
    if c2.button("📤 WITHDRAW BALANCE"): st.session_state.action_type = "WITHDRAW BALANCE"
    if c3.button("🔄 REINVEST"): st.session_state.action_type = "REINVEST"

    if st.button("LOGOUT"): 
        st.session_state.user = None
        st.rerun()
        
    if st.session_state.action_type == "DEPOSIT CAPITAL":
        with st.form("d"):
            amt_d = st.number_input("Amount", 1000.0)
            st.file_uploader("Receipt", type=['jpg','png','jpeg'])
            if st.form_submit_button("SUBMIT"):
                data.setdefault('pending_actions', []).append({"type":"DEPOSIT", "amount":amt_d, "request_id":req_id})
                data.setdefault('history', []).append({"type":"DEPOSIT", "amount":amt_d, "status":"Waiting Approval", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data)
                st.session_state.action_type=None
                st.rerun()

    if st.session_state.action_type == "WITHDRAW BALANCE":
        with st.form("w"):
            amt_w = st.number_input("Amount", 1000.0, max_value=max(1000.0, wallet))
            bank = st.text_input("Bank name, Account name, Account number")
            if st.form_submit_button("SUBMIT"):
                if wallet >= amt_w:
                    data['wallet'] = max(0.0, wallet - amt_w)
                    data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "request_id":req_id, "details":bank})
                    data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt_w, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data)
                    st.session_state.action_type=None
                    st.rerun()

    if st.session_state.action_type == "REINVEST":
        with st.form("r"):
            amt_r = st.number_input("Reinvest", 0.0, max_value=max(0.0, wallet))
            if st.form_submit_button("CONFIRM"):
                if wallet >= amt_r and amt_r > 0:
                    data['wallet'] = max(0.0, wallet - amt_r)
                    data.setdefault('pending_actions', []).append({"type":"REINVEST", "amount":amt_r, "request_id":req_id})
                    data.setdefault('history', []).append({"type":"REINVEST", "amount":amt_r, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data)
                    st.session_state.action_type=None
                    st.rerun()

    st.markdown("---")
    st.markdown("""
    <style>
    /* This targets the buttons specifically */
    .stButton > button {
        font-size: 8px !important
        height: 25px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        min-height: 25px !important;
        line-height: 25px !important;
    }
    </style>
    """, unsafe_allow_html=True)
            
    st.subheader("🚀 RUNNING CAPITALS")
    for idx, item in enumerate(list(data.get('inv', []))):
        start_dt = datetime.fromisoformat(item['start_time'])
        end_dt = start_dt + timedelta(days=7)
        pull_out_end = end_dt + timedelta(hours=1)
        
        elapsed = (ph_now - start_dt).total_seconds()
        progress = min(1.0, elapsed / 604800)
        roi_total = item['amount'] * 0.20
        live_profit = progress * roi_total

        st.markdown(f"""
        <div style="background-color: #1c2128; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff88; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #8b949e; font-weight: bold;">CAPITAL: ₱{item['amount']:,.2f}</span>
                <span style="color: #00ff88; font-weight: bold;">ROI: ₱{roi_total:,.2f}</span>
            </div>
            <div style="margin-top: 5px; color: white; font-size: 0.9em;">LIVE PROFIT: ₱{live_profit:,.2f}</div>
            <div style="color: #e3b341; font-size: 0.8em; margin-top: 10px;">
                ⚠️ Capital and interest available to pull out on:<br>
                {end_dt.strftime('%Y-%m-%d %I:%M %p')} until {pull_out_end.strftime('%I:%M %p')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        is_op = end_dt <= ph_now <= pull_out_end
        ca, cb = st.columns(2)
        
        if ca.button(f"📥 CLAIM INTEREST (available on date stated above)", key=f"interest_{idx}", disabled=not is_op, use_container_width=True):
            data['wallet'] = data.get('wallet', 0) + roi_total
            item['start_time'] = ph_now.isoformat()
            save(st.session_state.user, data)
            st.rerun()
            
        if cb.button(f"📤 PULL OUT CAPITAL (available on date stated above)", key=f"pull_{idx}", disabled=not is_op, use_container_width=True):
            data['wallet'] = data.get('wallet', 0) + (item['amount'] + interest_total)
            data['inv'].pop(idx)
            save(st.session_state.user, data)
            st.rerun()

    st.subheader("📜 HISTORY")
    for h in reversed(data.get('history', [])):
        st.markdown(f"<div class='hist-card'>{h['type']} | ₱{h['amount']:,.2f} | {h['status']}</div>", unsafe_allow_html=True)

elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("GO"):
            r = load_reg()
            if u in r and str(r[u]['pin']) == p: 
                st.session_state.user = u
                st.rerun()
    with t2:
        inv_n = st.session_state.get('captured_ref', 'OFFICIAL')
        st.write(f"Invitor: {inv_n}")
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("PIN (4 digits)", type="password", max_chars=4)
        if st.button("CREATE"):
            save(nu, {"pin":np, "wallet":0.0, "ref_by":inv_n, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Done!")
            st.rerun()
else:
    # --- ADMIN ACCESS POINT FIXED ---
    if st.button("🔒"): 
        st.session_state.page = "boss_key"
        st.rerun()
    
    st.title("ISMEX PHILIPPINES")
    st.write("International Stock Market Exchange")
    if st.button("🚀 ENTER ISMEX NOW", use_container_width=True): 
        st.session_state.page = "auth"
        st.rerun()
    st.caption("Secure v5.0")
                            
