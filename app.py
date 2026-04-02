import streamlit as st
import json
import os
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: CORE DATA ENGINE
# ==========================================
def load_registry():
    if os.path.exists("bpsm_registry.json"):
        try:
            with open("bpsm_registry.json", "r") as f: return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open("bpsm_registry.json", "w") as f: 
        json.dump(reg, f, indent=4, default=str)

# State initialization
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sub_page' not in st.session_state: st.session_state.sub_page = "select"
if 'action_type' not in st.session_state: st.session_state.action_type = None

# ==========================================
# BLOCK 2: UI STYLES
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #00ff88; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE ROUTING
# ==========================================

# --- ADMIN PANEL ---
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
    
    reg = load_registry()
    st.subheader("🔔 PENDING APPROVALS")
    found_pending = False
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(pending_list):
            found_pending = True
            with st.expander(f"{action['type']} - {username} (₱{action.get('amount', 0):,.2f})"):
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW": u_data['wallet'] += action['amount']
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()

# --- USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1: st.write(f"Logged in as: **{data.get('full_name')}**")
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #00ff88;">
            <p style="color:#8c8f99; font-size:14px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data['wallet']:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            amt_d = st.number_input("Amount", min_value=100.0)
            if st.form_submit_button("Submit"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": str(datetime.now())})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    # --- RUNNING CAPITALS SECTION ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active:
        st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in enumerate(active):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            
            st.markdown(f"""
                <div class='hist-card'>
                    <b>RUNNING CAPITAL</b>: ₱{a['amount']:,.2f}<br>
                    <small><b>Started:</b> {start_dt.strftime('%Y-%m-%d %H:%M')}</small><br>
                    <small><b>Matures:</b> {end_dt.strftime('%Y-%m-%d %H:%M')}</small>
                </div>
            """, unsafe_allow_html=True)
            
            if now < end_dt:
                st.write(f"⏳ Time Remaining: {str(end_dt - now).split('.')[0]}")
            else:
                if st.button(f"📥 PULL OUT ₱{a['amount']*1.20:,.2f}", key=f"p_{idx}"):
                    data['wallet'] += (a['amount'] * 1.20)
                    active.pop(idx)
                    update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 TRANSACTION HISTORY")
    t1, t2 = st.tabs(["⏳ Waiting", "✅ Approved"])
    with t1:
        for p in data.get('pending_actions', []):
            st.write(f"**{p['type']}**: ₱{p['amount']:,.2f} - {p['date'][:16]}")

# --- LOGIN / REGISTER ---
elif st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    if st.button("Back"): st.session_state.page = "ad"; st.rerun()
    u = st.text_input("USERNAME").upper().strip()
    p = st.text_input("PIN", type="password")
    
    if st.button("LOGIN"):
        reg = load_registry()
        if u in reg and str(reg[u]['pin']) == str(p):
            st.session_state.user = u; st.rerun()
        else:
            st.error("Invalid Username or PIN")
            
    if st.button("REGISTER NEW ACCOUNT"):
        reg = load_registry()
        if u in reg:
            st.warning(" Account exist ")
        else:
            reg[u] = {"pin": p, "wallet": 0.0, "inv": [], "full_name": u, "pending_actions": []}
            update_user(u, reg[u]); st.success("Created!")

# --- SIMPLE ADVERTISEMENT FRONT PAGE ---
else:
    st.markdown("# ISMEX OFFICIAL")
    st.markdown("### Transform your initial investment into a powerhouse of growth through our precision-engineered market cycles. Watch your capital accelerate in a secure environment where every cent is optimized for maximum, safe accumulation.")
    st.divider()
    
    st.info("### 🚀 Grow your capital by 20% every 7 days. Experience rapid capital acceleration through our high-performance exchange, designed to maximize your growth every cycle. Invest with total peace of mind using our institutional-grade security and seamless, transparent withdrawal systems.")
    st.write("Join the world's most advanced automated trading exchange. Turn your static savings into active wealth.")
    
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 GET STARTED / LOGIN", use_container_width=True):
        st.session_state.page = "login"; st.rerun()

    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
            
