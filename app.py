import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# ==========================================================
# ZONE 1: UI & INITIALIZATION
# ==========================================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

# Crash Prevention: Initialize all session keys
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
    .inv-card {
        background: #1e222d; padding: 20px; border-radius: 15px; 
        border-top: 4px solid #00ff88; margin-bottom: 15px;
    }
    .live-roi { color: #00ff88; font-family: monospace; font-size: 1.4rem; font-weight: bold; }
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

# ==========================================================
# ZONE 3: ADMIN PANEL (COMMISSION & APPROVALS)
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
                    
                    # 30% First Deposit Commission Logic
                    if act['type'] == "DEPOSIT" and not u_data.get('has_deposited', False):
                        inviter = u_data.get('ref_by')
                        if inviter in reg:
                            comm = act['amount'] * 0.30
                            reg[inviter]['wallet'] = reg[inviter].get('wallet', 0) + comm
                            reg[inviter].setdefault('history', []).append({
                                "type": "COMMISSION", "amount": comm, "from": u, "date": now, "status": "CONFIRMED"
                            })
                            save(inviter, reg[inviter])
                        u_data['has_deposited'] = True

                    if act['type'] in ["DEPOSIT", "REINVEST"]:
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "date": now})
                    
                    for h in u_data.get('history', []):
                        if h.get('id') == act.get('id'): h['status'] = "CONFIRMED"
                    u_data['pending'].pop(idx); save(u, u_data); st.rerun()

# ==========================================================
# ZONE 4: USER DASHBOARD (LIVE ROI & SMART LOCKS)
# ==========================================================
elif st.session_state.user:
    reg = load_reg()
    data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0))
    ph_now = datetime.now() + timedelta(hours=8)
    
    st.markdown(f"<div class='balance-box'><h3>WALLET BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    # LIVE ROI SECTION
    st.subheader("🚀 ACTIVE RUNNING CAPITAL")
    active_invs = data.get('inv', [])
    updated_invs = []
    changes = False

    for idx, inv in enumerate(active_invs):
        start = datetime.fromisoformat(inv['date'])
        end_time = start + timedelta(days=7)
        expiry = end_time + timedelta(hours=1)
        
        # MATH
        elapsed = (ph_now - start).total_seconds()
        is_open = end_time <= ph_now <= expiry
        
        if ph_now > expiry:
            # AUTO REINVEST
            new_cap = inv['amount'] * 1.20
            updated_invs.append({"amount": new_cap, "date": ph_now.isoformat()})
            data.setdefault('history', []).append({"type": "AUTO_REI", "amount": new_cap, "date": ph_now.isoformat()})
            changes = True; continue

        # UI
        live_val = inv['amount'] * (min(1.0, elapsed/(7*86400))) * 0.20
        with st.container():
            st.markdown(f"""
                <div class="inv-card">
                    <small>CAPITAL: ₱{inv['amount']:,.2f}</small><br>
                    <span class="live-roi">₱{live_val:,.2f}</span><br>
                    <small>Unlocked at: {end_time.strftime('%I:%M %p, %b %d')}</small>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button(f"Withdraw ROI (₱{inv['amount']*0.20:,.2f})", key=f"r_{idx}", disabled=not is_open):
                data['wallet'] = wallet + (inv['amount']*0.20); inv['date'] = ph_now.isoformat()
                save(st.session_state.user, data); st.rerun()
            if c2.button(f"Withdraw Capital (₱{inv['amount']*1.20:,.2f})", key=f"c_{idx}", disabled=not is_open):
                data['wallet'] = wallet + (inv['amount']*1.20); changes=True; continue
            
            updated_invs.append(inv)

    if changes: data['inv'] = updated_invs; save(st.session_state.user, data); st.rerun()

# ==========================================================
# ZONE 5: AUTH & AUTO-FILL REFERRAL
# ==========================================================
elif st.session_state.page == "auth":
    params = st.query_params
    detected_ref = params.get("ref", "")

    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOG IN"):
            r = load_reg()
            if u in r and str(r[u].get('pin')) == p:
                st.session_state.user = u; st.rerun()
    with t2:
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("4-DIGIT PIN", type="password", max_chars=4)
        # AUTO-FILLED
        nr = st.text_input("INVITED BY", value=detected_ref).upper().strip()
        if st.button("REGISTER"):
            save(nu, {"pin": np, "wallet": 0.0, "inv": [], "history": [], "pending": [], "ref_by": nr, "has_deposited": False})
            st.success("Success! Please Login.")
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 START NOW"): st.session_state.page = "auth"; st.rerun()
    if st.button("⛔") and st.text_input("Admin", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
                            
