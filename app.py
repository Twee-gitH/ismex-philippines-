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
    .ref-container {
        background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

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
                    
                    # Confirm status in history
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                        
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()
                
                if c2.button("❌ REJECT", key=f"rj_{u}_{idx}"):
                    # Return money to wallet if it was a withdrawal/reinvest
                    if act['type'] in ["WITHDRAW", "REINVEST"]:
                        u_data['wallet'] = u_data.get('wallet', 0) + act['amount']
                    
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "REJECTED"
                        
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()

# ==========================================================
# ZONE 4: USER DASHBOARD
# ==========================================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    # ADVERTISEMENT HEADER
    st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h1 style='color: #00ff88;'>STOP WORKING FOR MONEY.</h1>
            <h2 style='color: #ffffff;'>Let Your Money Work for You.</h2>
            <p style='font-size: 1.1rem;'>The stock market is the ultimate wealth engine. Own a piece of innovation and watch your value increase rapidly.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action = "REI"

    if st.session_state.action == "DEP":
        with st.form("d_f"):
            amt = st.number_input("Amount", 500.0)
            receipt = st.file_uploader("Upload Receipt Image", type=['jpg','png','jpeg'])
            if st.form_submit_button("SUBMIT"):
                if receipt:
                    rid = ph_now.strftime("%H%M%S")
                    data.setdefault('pending', []).append({"type": "DEPOSIT", "amount": amt, "id": rid})
                    data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else: st.error("Receipt required!")

    if st.session_state.action == "WIT":
        with st.form("w_f"):
            amt = st.number_input("Amount", 500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank/GCash Name")
            acc_name = st.text_input("Account Name")
            acc_num = st.text_input("Account Number")
            if st.form_submit_button("REQUEST"):
                if wallet >= amt:
                    rid = ph_now.strftime("%H%M%S")
                    data['wallet'] = wallet - amt # Deduct now to prevent negative
                    details = f"{bank} | {acc_name} | {acc_num}"
                    data.setdefault('pending', []).append({"type": "WITHDRAW", "amount": amt, "id": rid, "details": details})
                    data.setdefault('history', []).append({"type": "WITHDRAW", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else: st.error("Insufficient Balance!")

    if st.session_state.action == "REI":
        with st.form("r_f"):
            amt = st.number_input("Reinvest Amount", 500.0, max_value=max(500.0, wallet))
            if st.form_submit_button("CONFIRM REINVEST"):
                if wallet >= amt:
                    rid = ph_now.strftime("%H%M%S")
                    data['wallet'] = wallet - amt
                    data.setdefault('pending', []).append({"type": "REINVEST", "amount": amt, "id": rid})
                    data.setdefault('history', []).append({"type": "REINVEST", "amount": amt, "id": rid, "status": "PENDING", "date": ph_now.strftime("%Y-%m-%d")})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else: st.error("Insufficient Balance!")

    # REFERRAL SECTION
    st.markdown("---")
    st.subheader("👥 REFERRAL SYSTEM")
    ref_link = f"https://ismex.streamlit.app/?ref={st.session_state.user}"
    st.markdown(f"""<div class='ref-container'><strong>Share Link:</strong><br><code>{ref_link}</code></div>""", unsafe_allow_html=True)
    
    ref_list = []
    for n, i in reg.items():
        if i.get('ref_by') == st.session_state.user:
            for inv in i.get('inv', []):
                ref_list.append({"User": n, "Investment": inv['amount'], "Bonus (30%)": inv['amount']*0.3})
    if ref_list: st.table(ref_list)

    # ROI LOGIC
    st.markdown("---")
    st.subheader("🚀 ACTIVE INVESTMENTS")
    for idx, inv in enumerate(list(data.get('inv', []))):
        start = datetime.fromisoformat(inv.get('date'))
        roi = inv['amount'] * 1.20
        prog = min(1.0, (ph_now - start).total_seconds() / (7*86400))
        st.write(f"₱{inv['amount']:,} → ₱{roi:,.2f}")
        st.progress(prog)
        if ph_now >= start + timedelta(days=7) and st.button(f"CLAIM ₱{roi:,.2f}", key=f"c_{idx}"):
            data['wallet'] = wallet + roi
            data['inv'].pop(idx); save(st.session_state.user, data); st.rerun()

    # HISTORY
    st.markdown("---")
    st.subheader("📜 HISTORY")
    if data.get('history'): st.table(data['history'][::-1])

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================================
# ZONE 5: AUTH & LANDING
# ==========================================================
elif st.session_state.page == "auth":
    # AUTO-CAPTURE REFERRAL FROM URL
    params = st.query_params
    ref_from_url = params.get("ref", "")

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
        # AUTO-FILLED FIELD
        nr = st.text_input("REFERRAL CODE", value=ref_from_url).upper().strip()
        if st.button("REGISTER"):
            save(nu, {"pin": np, "wallet": 0.0, "inv": [], "history": [], "pending": [], "ref_by": nr})
            st.success("Registration Success!"); st.session_state.page = "auth"
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 CLICK TO START"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("execution error", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                        
