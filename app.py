import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================================
# ZONE 1: UI & THE GITHUB SHIELD
# ==========================================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2.5rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,255,136,0.1);
    }
    .main .block-container { padding-bottom: 350px !important; }
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
    setInterval(shield, 50);
    </script>
    """, height=0)

# ==========================================================
# ZONE 2: DATABASE CONNECTIVITY
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

for k, v in [('user',None), ('page','landing'), ('is_boss',False), ('action',None)]:
    if k not in st.session_state: st.session_state[k] = v

# ==========================================================
# ZONE 3: ADMIN PANEL (FULL APPROVAL LOGIC)
# ==========================================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, u_data in reg.items():
        pend = u_data.get('pending', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"REQ: {act['type']} - {u} (₱{act.get('amount',0):,.2f})"):
                if 'details' in act: st.code(act['details'])
                
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", key=f"ap_{u}_{idx}"):
                    now = (datetime.now() + timedelta(hours=8)).isoformat()
                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "date": now})
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("❌ REJECT", key=f"rj_{u}_{idx}"):
                    if act['type'] in ["WITHDRAW", "REINVEST"]:
                        u_data['wallet'] = u_data.get('wallet', 0) + act['amount']
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()

# ==========================================================
# ZONE 4: USER DASHBOARD (RESTORED LOGICS)
# ==========================================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action = "REI"

    # RESTORED: DEPOSIT + RECEIPT UPLOADER
    if st.session_state.action == "DEP":
        with st.form("d_f"):
            amt = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Upload Receipt Image", type=['jpg','png','jpeg'])
            if st.form_submit_button("SUBMIT"):
                if receipt:
                    rid = ph_now.strftime("%f")
                    data.setdefault('pending', []).append({"type": "DEPOSIT", "amount": amt, "id": rid})
                    data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else: st.error("Receipt required!")

    # RESTORED: WITHDRAW LOGIC
    if st.session_state.action == "WIT":
        with st.form("w_f"):
            amt = st.number_input("Amount", 500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank/GCash Details")
            if st.form_submit_button("REQUEST"):
                rid = ph_now.strftime("%f")
                data['wallet'] = wallet - amt
                data.setdefault('pending', []).append({"type": "WITHDRAW", "amount": amt, "id": rid, "details": bank})
                data.setdefault('history', []).append({"type": "WITHDRAW", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action = None; st.rerun()

    # RESTORED: REINVEST LOGIC
    if st.session_state.action == "REI":
        with st.form("r_f"):
            amt = st.number_input("Reinvest Amount", 500.0, max_value=max(500.0, wallet))
            if st.form_submit_button("CONFIRM REINVEST"):
                rid = ph_now.strftime("%f")
                data['wallet'] = wallet - amt
                data.setdefault('pending', []).append({"type": "REINVEST", "amount": amt, "id": rid})
                data.setdefault('history', []).append({"type": "REINVEST", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action = None; st.rerun()

    # RESTORED: 30% REFERRAL LOGIC
    st.markdown("---")
    st.subheader("👥 REFERRALS (30% COMMISSION)")
    for n, i in reg.items():
        if i.get('ref_by') == st.session_state.user and i.get('inv'):
            comm = i['inv'][0]['amount'] * 0.30
            st.success(f"₱{comm:,.2f} from {n}")

    # ROI (FIXED KEYERROR FROM SCREENSHOT)
    st.markdown("---")
    st.subheader("🚀 INVESTMENTS (20% WEEKLY)")
    for idx, inv in enumerate(list(data.get('inv', []))):
        raw_date = inv.get('date') or inv.get('start_time')
        if raw_date:
            start = datetime.fromisoformat(raw_date)
            roi = inv['amount'] * 1.20
            prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
            st.write(f"₱{inv['amount']:,} → ₱{roi:,.2f}")
            st.progress(prog)
            if ph_now >= start + timedelta(days=7) and st.button(f"CLAIM ₱{roi:,.2f}", key=f"c_{idx}"):
                data['wallet'] = wallet + roi
                data['inv'].pop(idx); save(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================================
# ZONE 5: AUTH & LANDING
# ==========================================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("ENTER"):
            r = load_reg()
            if u in r and str(r[u].get('pin')) == p:
                st.session_state.user = u; st.rerun()
    with t2:
        nu = st.text_input("NEW FULL NAME").upper().strip()
        np = st.text_input("SET 4-DIGIT PIN", type="password", max_chars=4)
        if st.button("REGISTER"):
            save(nu, {"pin": np, "wallet": 0.0, "inv": [], "history": [], "pending": []})
            st.success("Success!"); st.session_state.page = "auth"
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 CLICK TO START"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Admin Key", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                    
