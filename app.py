import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================================
# ZONE 1: STYLING & GITHUB FRONT-PAGE SHIELD (UI)
# ==========================================================
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
    /* Essential space for the GitHub Floor */
    .main .block-container { padding-bottom: 350px !important; }
    </style>
    """, unsafe_allow_html=True)

# THE GITHUB INJECTION: This covers the Streamlit icons at the bottom
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
    setInterval(maintainWall, 50);
    </script>
    """, height=0)

# ==========================================================
# ZONE 2: DATABASE & SESSION MANAGEMENT (CORE LOGIC)
# ==========================================================
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

for k, v in [('user',None), ('page','landing'), ('is_boss',False), ('admin_mode',False), ('action',None)]:
    if k not in st.session_state: st.session_state[k] = v

if "ref" in st.query_params:
    st.session_state["ref_id"] = st.query_params["ref"].replace("+", " ").upper()

# ==========================================================
# ZONE 3: ADMIN APPROVAL SYSTEM (LOGIC)
# ==========================================================
if st.session_state.is_boss:
    st.title("👑 ISMEX SYSTEM CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, u_data in reg.items():
        pend = u_data.get('pending', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"🔴 {act['type']} - {u}"):
                st.write(f"AMOUNT: ₱{act['amount']:,.2f}")
                if 'bank' in act: st.code(act['bank'])
                
                c1, c2 = st.columns(2)
                if c1.button("APPROVE", key=f"app_{u}_{idx}"):
                    ph_now = (datetime.now() + timedelta(hours=8)).isoformat()
                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "date": ph_now})
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("REJECT", key=f"rej_{u}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]: u_data['wallet'] = u_data.get('wallet',0) + act['amount']
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()

# ==========================================================
# ZONE 4: DASHBOARD, 30% REF, & 20% ROI (LOGIC & UI)
# ==========================================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.title(f"👋 {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><p style='color:#888;'>AVAILABLE BALANCE</p><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    if cols[0].button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if cols[1].button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if cols[2].button("🔄 REINVEST"): st.session_state.action = "REI"

    if st.session_state.action == "DEP":
        with st.form("d_f"):
            amt = st.number_input("Deposit Amount", 500.0)
            if st.form_submit_button("SUBMIT"):
                rid = ph_now.strftime("%f")
                data.setdefault('pending', []).append({"type": "DEPOSIT", "amount": amt, "id": rid})
                data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action = None; st.rerun()

    # --- THE 30% REFERRAL LOGIC ---
    st.markdown("---")
    st.subheader("👥 YOUR REFERRAL NETWORK")
    ref_url = f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={st.session_state.user.replace(' ','+')}"
    st.code(ref_url)
    
    for name, u_data in reg.items():
        if u_data.get('ref_by') == st.session_state.user and u_data.get('inv'):
            comm = u_data['inv'][0]['amount'] * 0.30
            st.markdown(f"<div class='hist-card' style='border-left-color:#00ff88;'>+ ₱{comm:,.2f} Commission from <b>{name}</b></div>", unsafe_allow_html=True)

    # --- THE 20% WEEKLY ROI LOGIC (FIXED) ---
    st.markdown("---")
    st.subheader("🚀 ACTIVE INVESTMENTS (20% WEEKLY)")
    invs = data.get('inv', [])
    for idx, i in enumerate(list(invs)):
        # Safety check for the KeyError: handles 'date' or 'start_time'
        raw_date = i.get('date') or i.get('start_time')
        if raw_date:
            start_date = datetime.fromisoformat(raw_date)
            end_date = start_date + timedelta(days=7)
            roi = i['amount'] * 1.20
            
            prog = min(1.0, (ph_now - start_date).total_seconds() / (7 * 86400))
            st.markdown(f"**Capital: ₱{i['amount']:,.2f}** → **Target: ₱{roi:,.2f}**")
            st.progress(prog)
            
            if ph_now >= end_date:
                if st.button(f"CLAIM ROI ₱{roi:,.2f}", key=f"roi_{idx}"):
                    data['wallet'] = wallet + roi
                    data['inv'].pop(idx)
                    save(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================================
# ZONE 5: AUTHENTICATION & LANDING (UI)
# ==========================================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u_in = st.text_input("FULL NAME").upper().strip()
        p_in = st.text_input("PIN", type="password")
        if st.button("ENTER"):
            r = load_reg()
            if u_in in r and str(r[u_in].get('pin')) == p_in:
                st.session_state.user = u_in; st.rerun()
    with t2:
        inv_by = st.session_state.get('ref_id', 'OFFICIAL')
        st.info(f"Invited by: {inv_by}")
        nu = st.text_input("NEW FULL NAME").upper().strip()
        np = st.text_input("SET 4-DIGIT PIN", type="password", max_chars=4)
        if st.button("REGISTER ACCOUNT"):
            save(nu, {"pin": np, "wallet": 0.0, "ref_by": inv_by, "inv": [], "history": [], "pending": []})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES")
    if st.button("🚀 CLICK TO START"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode:
        if st.text_input("''execution error''", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
                      
