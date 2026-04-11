import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================================
# ZONE 1: UI & THE GITHUB SHIELD (Restored Advertisement)
# ==========================================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

# Initialize state to prevent crashes
for k, v in [('user', None), ('page', 'landing'), ('is_boss', False), ('action', None)]:
    if k not in st.session_state: st.session_state[k] = v

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], footer { visibility: hidden !important; display: none !important; }
    .stApp { background-color: #0e1117 !important; color: white; }
    .balance-box {
        background: linear-gradient(135deg, #1e222d 0%, #0e1117 100%);
        padding: 2.5rem; border-radius: 20px; border: 2px solid #00ff88;
        text-align: center; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,255,136,0.1);
    }
    .inv-card { background: #1e222d; padding: 20px; border-radius: 15px; border-top: 4px solid #00ff88; margin-bottom: 15px; }
    .live-roi { color: #00ff88; font-family: monospace; font-size: 1.4rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# ZONE 2: DB CONNECTIVITY
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
def load_reg(): return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
def save(n, d): db.collection("investors").document(n).set(d)

# ==========================================================
# ZONE 4: USER DASHBOARD
# ==========================================================
if st.session_state.user:
    # --- ADVERTISEMENT HEADER (RESTORED) ---
    st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h1 style='color: #00ff88; margin-bottom:0;'>STOP WORKING FOR MONEY.</h1>
            <h2 style='color: #ffffff; margin-top:0;'>Let Your Money Work for You.</h2>
            <p style='font-size: 1.1rem; color: #8b949e;'>The stock market is the ultimate wealth engine. Own a piece of innovation and watch your value increase rapidly.</p>
        </div>
    """, unsafe_allow_html=True)

    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.markdown(f"<div class='balance-box'><h3>WALLET BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action = "REI"

    # Action Logic (Withdraw/Reinvest) includes Wallet Validation to fix your negative balance
    if st.session_state.action == "WIT":
        with st.form("w_f"):
            amt = st.number_input("Amount", 500.0)
            bank = st.text_area("Payout Details")
            if st.form_submit_button("SUBMIT"):
                if wallet >= amt:
                    data['wallet'] = wallet - amt
                    data.setdefault('pending', []).append({"type":"WITHDRAW", "amount":amt, "id":ph_now.strftime("%H%M%S"), "details":bank})
                    data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt, "status":"PENDING", "date":ph_now.isoformat()})
                    save(st.session_state.user, data); st.session_state.action = None; st.rerun()
                else: st.error("Insufficient Balance!")

    # ==========================================================
    # REFERRAL LOGIC & TABLE (RESTORED & IMPROVED)
    # ==========================================================
    st.markdown("---")
    st.subheader("👥 YOUR REFERRAL NETWORK")
    ref_link = f"https://ismex.streamlit.app/?ref={st.session_state.user}"
    st.code(ref_link, language=None)
    
    ref_table = []
    for u, u_data in reg.items():
        if u_data.get('ref_by') == st.session_state.user:
            # Find their first confirmed deposit
            f_dep = next((h['amount'] for h in u_data.get('history', []) if h['type'] == "DEPOSIT" and h['status'] == "CONFIRMED"), 0.0)
            ref_table.append({"Member": u, "1st Deposit": f"₱{f_dep:,.2f}", "Commission (30%)": f"₱{f_dep*0.3:,.2f}"})
    if ref_table: st.table(ref_table)

    # ==========================================================
    # ACTIVE INVESTMENTS (CRASH-PROOF)
    # ==========================================================
    st.markdown("---")
    st.subheader("🚀 ACTIVE RUNNING CAPITAL")
    active_invs = data.get('inv', [])
    updated_invs = []
    changed = False

    for idx, inv in enumerate(active_invs):
        d_val = inv.get('date')
        if not d_val: continue # Skip corrupt entries that cause KeyErrors
        
        start = datetime.fromisoformat(d_val)
        end_time = start + timedelta(days=7)
        expiry = end_time + timedelta(hours=1)
        is_open = end_time <= ph_now <= expiry
        
        if ph_now > expiry:
            new_val = inv['amount'] * 1.20
            updated_invs.append({"amount": new_val, "date": ph_now.isoformat()})
            data.setdefault('history', []).append({"type":"AUTO_REI", "amount":new_val, "date":ph_now.isoformat()})
            changed = True; continue

        # UI for individual Investment
        elapsed = (ph_now - start).total_seconds()
        live_roi = inv['amount'] * (min(1.0, elapsed/(7*86400))) * 0.20
        
        with st.container():
            st.markdown(f"""<div class="inv-card">
                <small>CAPITAL: ₱{inv['amount']:,.2f}</small><br>
                <span class="live-roi">₱{live_roi:,.2f}</span><br>
                <small>Ready: {end_time.strftime('%b %d, %I:%M %p')}</small></div>""", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button(f"ROI Only (₱{inv['amount']*0.2:,.2f})", key=f"r_{idx}", disabled=not is_open):
                data['wallet'] = wallet + (inv['amount']*0.2); inv['date'] = ph_now.isoformat()
                save(st.session_state.user, data); st.rerun()
            if c2.button(f"Full Capital (₱{inv['amount']*1.2:,.2f})", key=f"c_{idx}", disabled=not is_open):
                data['wallet'] = wallet + (inv['amount']*1.2); changed = True; continue
            updated_invs.append(inv)

    if changed: data['inv'] = updated_invs; save(st.session_state.user, data); st.rerun()
    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================================
# ZONE 5: AUTH & AUTO-FILL INVITER
# ==========================================================
elif st.session_state.page == "auth":
    params = st.query_params
    url_ref = params.get("ref", "")
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t2:
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("PIN", type="password", max_chars=4)
        # Auto-detects inviter from URL link
        nr = st.text_input("INVITED BY", value=url_ref).upper().strip()
        if st.button("CREATE ACCOUNT"):
            save(nu, {"pin":np, "wallet":0.0, "inv":[], "history":[], "pending":[], "ref_by":nr, "has_deposited":False})
            st.success(f"Success! Welcome aboard.")
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 GET STARTED"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Admin", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
        
