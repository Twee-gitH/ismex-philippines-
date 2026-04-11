import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import time

# ==========================================
# 1. UI & SECURE SHIELD (PRESERVED)
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
    .cap-card {
        background: #1c2128; padding: 20px; border-radius: 15px;
        margin-bottom: 15px; border: 1px solid #30363d;
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
            s.style.cssText = 'position:fixed;bottom:0;left:0;width:100vw;height:130px;background:#0e1117;z-index:2147483647;pointer-events:none;';
            p.body.appendChild(s);
        }
        const b = p.querySelector('.viewerBadge_container__1QSob');
        if (b) b.style.display = 'none';
    };
    setInterval(shield, 100);
    </script>
    """, height=0)

# ==========================================
# 2. DATABASE & STATE (PRESERVED)
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
def load_reg(): return {doc.id: doc.to_dict() for doc in db.collection("investors").stream()}
def save(n, d): db.collection("investors").document(n).set(d)

for k, v in [('user',None), ('page','landing'), ('is_boss',False), ('action_type',None)]:
    if k not in st.session_state: st.session_state[k] = v

if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# ==========================================
# 3. ADMIN PANEL (FULL MEMBER OVERSIGHT)
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN COMMAND CENTER")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    reg = load_reg()
    t1, t2 = st.tabs(["📥 APPROVALS", "👥 MASTER LIST"])
    with t1:
        for u, u_data in reg.items():
            pend = u_data.get('pending_actions', [])
            for idx, act in enumerate(list(pend)):
                with st.expander(f"{act['type']} - {u}"):
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
                        u_data['pending_actions'].pop(idx); save(u, u_data); st.rerun()
    with t2:
        st.subheader("ALL MEMBER PINS & BALANCES")
        st.table([{"NAME": n, "PIN": i.get('pin'), "WALLET": i.get('wallet')} for n, i in reg.items()])
        audit_user = st.selectbox("Audit Full History", list(reg.keys()))
        if audit_user: st.json(reg[audit_user].get('history', []))

# ==========================================
# 4. USER DASHBOARD (WITH LIVE RUNNING CAPITAL)
# ==========================================
elif st.session_state.user:
    reg = load_reg(); data = reg.get(st.session_state.user, {})
    wallet = float(data.get('wallet', 0.0))
    ph_now = datetime.now() + timedelta(hours=8)
    req_id = ph_now.strftime("%f")

    st.markdown(f"<div class='balance-box'><h3>AVAILABLE BALANCE</h3><h1>₱{wallet:,.2f}</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if col2.button("📤 WITHDRAW"): st.session_state.action_type = "WIT"
    if col3.button("🔄 REINVEST"): st.session_state.action_type = "REI"

    # --- FORMS (PRESERVED) ---
    if st.session_state.action_type == "WIT":
        with st.form("w"):
            amt_w = st.number_input("Amount", 500.0, max_value=max(500.0, wallet))
            bank = st.text_input("Bank Details")
            if st.form_submit_button("SUBMIT"):
                data['wallet'] -= amt_w
                data.setdefault('pending_actions', []).append({"type":"WITHDRAW", "amount":amt_w, "request_id":req_id, "details":bank})
                data.setdefault('history', []).append({"type":"WITHDRAW", "amount":amt_w, "status":"PENDING", "request_id":req_id, "date":ph_now.strftime("%Y-%m-%d")})
                save(st.session_state.user, data); st.session_state.action_type=None; st.rerun()

    # --- LIVE RUNNING CAPITAL (NEW LOGIC) ---
    st.markdown("---")
    st.subheader("🚀 LIVE RUNNING CAPITALS")
    active_inv = data.get('inv', [])
    if not active_inv:
        st.info("No active running capital.")
    else:
        for idx, item in enumerate(list(active_inv)):
            start_dt = datetime.fromisoformat(item['start_time'])
            end_dt = start_dt + timedelta(days=7)
            expiry_dt = end_dt + timedelta(hours=1)
            
            # Real-Time Logic
            total_sec = 7 * 86400
            elapsed = (ph_now - start_dt).total_seconds()
            progress = min(1.0, elapsed / total_sec)
            roi_total = item['amount'] * 0.20
            live_roi = (elapsed / total_sec) * roi_total if elapsed < total_sec else roi_total

            # Auto-Reinvest (Compounding)
            if ph_now > expiry_dt:
                item['amount'] += roi_total
                item['start_time'] = ph_now.isoformat()
                save(st.session_state.user, data); st.rerun()

            with st.container():
                st.markdown("<div class='cap-card'>", unsafe_allow_html=True)
                c_a, c_b = st.columns([2, 1])
                with c_a:
                    st.write(f"**Capital:** ₱{item['amount']:,.2f} | **Live ROI:** ₱{live_roi:,.2f}")
                    st.progress(progress)
                with c_b:
                    is_open = end_dt <= ph_now <= expiry_dt
                    if ph_now < end_dt:
                        diff = end_dt - ph_now
                        st.caption(f"🔒 Opens in {diff.days}d {diff.seconds//3600}h {(diff.seconds//60)%60}m")
                    elif is_open:
                        st.success("🔓 WINDOW OPEN")
                    
                    if st.button(f"Claim ROI (₱{roi_total:,.2f})", key=f"roi_{idx}", disabled=not is_open):
                        data['wallet'] += roi_total
                        item['start_time'] = ph_now.isoformat()
                        save(st.session_state.user, data); st.rerun()
                    if st.button("Withdraw Capital", key=f"cap_{idx}", disabled=not is_open):
                        data['wallet'] += item['amount']
                        data['inv'].pop(idx)
                        save(st.session_state.user, data); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # --- NETWORK & HISTORY (PRESERVED) ---
    st.markdown("---")
    st.subheader("👥 MY NETWORK")
    ref_link = st.session_state.user.replace(' ', '+')
    st.code(f"https://ismex-philippines-internationalstockmarketexchange.streamlit.app/?ref={ref_link}")
    
    st.subheader("📜 HISTORY")
    for h in reversed(data.get('history', [])):
        st.markdown(f"<div class='hist-card'><b>{h['type']}</b> | ₱{h['amount']:,.2f} | {h['status']}</div>", unsafe_allow_html=True)

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# ==========================================
# 5. AUTH & LANDING
# ==========================================
elif st.session_state.page == "auth":
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            r = load_reg()
            if u in r and str(r[u]['pin']) == p: st.session_state.user = u; st.rerun()
    with t2:
        inv = st.session_state.get('captured_ref', 'OFFICIAL')
        nu = st.text_input("FULL NAME").upper().strip()
        np = st.text_input("PIN", type="password", max_chars=4)
        if st.button("REGISTER"):
            save(nu, {"pin":np, "wallet":0.0, "ref_by":inv, "inv":[], "history":[], "pending_actions":[], "has_deposited":False})
            st.success("Registered!"); st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 ENTER"): st.session_state.page = "auth"; st.rerun()
    with st.expander("⛔"):
        if st.text_input("Key", type="password") == "0102030405":
            if st.button("ADMIN"): st.session_state.is_boss = True; st.rerun()
        
