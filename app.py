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
if 'action_type' not in st.session_state: st.session_state.action_type = None

# ==========================================
# BLOCK 2: UI STYLES & ABSOLUTE LOCKDOWN
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

# Capture Referral
if "ref" in st.query_params:
    st.session_state.url_ref = st.query_params["ref"].replace("+", " ").upper().strip()
current_ref = st.session_state.get("url_ref", "")

# AGGRESSIVE CSS TO REMOVE ALL TRACES OF STREAMLIT BRANDING
st.markdown("""
    <style>
    /* REMOVE HEADER, FOOTER, AND ALL FLOATING BUTTONS/ICONS */
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important; display: none !important;}
    .stDeployButton {display:none !important;}
    
    /* TARGET THE SPECIFIC STATUS AND DECORATION BAR (WHERE THE FACE/CROWN LIVE) */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {display:none !important;}
    [data-testid="stStatusWidget"] {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    
    /* GLOBAL THEME FORCING */
    .stApp { background-color: #0e1117 !important; color: white !important; }
    
    /* MOBILE/MESSENGER BUTTON FIXES */
    div.stButton > button {
        background-color: #1c1e26 !important;
        color: #ffffff !important;
        border: 2px solid #333 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
    }

    /* DASHBOARD CARDS */
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 2px; border-left: 5px solid #00ff88; }
    .roi-text { color: #00ff88; font-weight: bold; float: right; font-size: 18px; }
    .live-profit { color: #8c8f99; font-size: 14px; margin-top: 5px; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 10px; }
    
    /* REFERRAL LINK BOX */
    .ref-link-box {
        background: #111; 
        padding: 15px; 
        border-radius: 8px; 
        border: 2px dashed #00ff88; 
        text-align: center; 
        margin-bottom: 25px;
    }

    /* HIDDEN ADMIN TOGGLE */
    .stButton>button:contains("⛔") { background-color: transparent !important; border: none !important; color: #0e1117 !important; width: 30px !important; }
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
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(list(pending_list)):
            with st.expander(f"{action['type']} - {username} - ₱{action.get('amount', 0):,.2f}"):
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        if not u_data.get('has_deposited'):
                            ref_name = u_data.get('referral')
                            if ref_name in reg:
                                commission = action['amount'] * 0.20
                                reg[ref_name].setdefault('commissions', []).append({
                                    "referee": username, "deposit": action['amount'],
                                    "amt": commission, "status": "UNCLAIMED"
                                })
                            u_data['has_deposited'] = True
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    
                    elif action['type'] == "COMMISSION_REQUEST":
                        u_data['wallet'] = u_data.get('wallet', 0.0) + action['amount']
                        c_idx = action.get('comm_index')
                        if c_idx is not None and len(u_data.get('commissions', [])) > c_idx:
                            u_data['commissions'][c_idx]['status'] = "CLAIMED"

                    u_data.setdefault('history', []).append({
                        "type": action['type'], "amount": action['amount'],
                        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"
                    })
                    u_data['pending_actions'].pop(idx)
                    with open("bpsm_registry.json", "w") as f: json.dump(reg, f, indent=4, default=str)
                    st.rerun()
                
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW": u_data['wallet'] += action['amount']
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data)
                    st.rerun()

# --- USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0

    st.write(f"Logged in as: **{st.session_state.user}**")
    if st.button("LOGOUT"):
        st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    # BALANCE DISPLAY
    st.markdown(f"""
        <div class="balance-box">
            <p style="color:#8c8f99; font-size:14px; margin-bottom:5px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data['wallet']:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    # --- DASHBOARD REFERRAL LINK ---
# This uses your new clean GitHub Pages URL
clean_base_url = "https://twee-gith.github.io/ISMEX-PHILIPPINES/" 

formatted_name = st.session_state.user.replace(" ", "+")
ref_link = f"{clean_base_url}?ref={formatted_name}"

st.markdown(f"""
    <div class="ref-link-box">
        <span style="color:#8c8f99; font-weight:bold;">🤝 SHARE YOUR LINK</span><br>
        <code style="color:#00ff88; font-size:14px;">{ref_link}</code>
    </div>
""", unsafe_allow_html=True)


    # Actions
    if st.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if st.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if st.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.info("💳 **GCASH:** 09XXXXXXXX | **NAME:** T*** S*** T.")
            amt_d = st.number_input("Amount", min_value=100.0)
            if st.form_submit_button("SEND TO ADMIN"):
                data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    # --- RUNNING CAPITALS ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in reversed(list(enumerate(active))):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            total_sec = (end_dt - start_dt).total_seconds()
            elapsed_sec = (now - start_dt).total_seconds()
            progress = min(1.0, elapsed_sec / total_sec)
            
            potential_profit = a['amount'] * 0.20
            live_profit = potential_profit * progress
            total_roi = a['amount'] + potential_profit
            
            st.markdown(f"""
                <div class='hist-card'>
                    <span class='roi-text'>ROI: ₱{total_roi:,.2f}</span>
                    <b>CAPITAL: ₱{a['amount']:,.2f}</b><br>
                    <div class='live-profit'>LIVE PROFIT: ₱{live_profit:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            st.progress(progress)
            
            if st.button(f"📥 PULL OUT ₱{total_roi:,.2f}", key=f"p_{idx}", disabled=not (progress >= 1.0)):
                data['wallet'] += total_roi
                data.setdefault('history', []).append({"type": "PULL_OUT", "amount": total_roi, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"})
                active.pop(idx)
                update_user(st.session_state.user, data); st.rerun()

    # --- PLACE THIS IN THE 'elif st.session_state.user:' SECTION ---

st.markdown("### 🤝 REFERRAL PROGRAM")

# YOUR NEW CLEAN GITHUB LINK
clean_base_url = "https://twee-gith.github.io/ISMEX-PHILIPPINES/" 
formatted_name = st.session_state.user.replace(" ", "+")
ref_link = f"{clean_base_url}?ref={formatted_name}"

# VISUAL BOX FOR THE LINK
st.markdown(f"""
    <div style="background: #111; padding: 20px; border-radius: 15px; border: 2px dashed #00ff88; text-align: center;">
        <p style="color: #8c8f99; margin-bottom: 10px; font-weight: bold;">YOUR UNIQUE REFERRAL LINK:</p>
        <code style="color: #00ff88; font-size: 16px; word-wrap: break-word;">{ref_link}</code>
    </div>
""", unsafe_allow_html=True)

# THE COPY BUTTON
if st.button("📋 CLICK TO COPY LINK"):
    # This dummy button provides a clear visual for users to tap
    st.write(f"**Link ready!** Long-press the green text above to copy.")
    st.toast("Link displayed above!")


    # --- HISTORY ---
    st.markdown("### 📜 TRANSACTION HISTORY")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ **{h.get('status', 'CONFIRMED')}**: ₱{h['amount']:,.2f} | {h['date']}")

elif st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    if st.button("Back"): st.session_state.page = "ad"; st.rerun()
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("FULL NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if u in reg and str(reg[u]['pin']) == str(p): st.session_state.user = u; st.rerun()
            else: st.error("Invalid Login")
    with t2:
        fn = st.text_input("NAME MIDDLE LAST").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        rn = st.text_input("REFERRAL NAME", value=current_ref).upper().strip()
        if st.button("REGISTER"):
            reg = load_registry()
            if fn and len(p1) == 6:
                reg[fn] = {"pin": p1, "wallet": 0.0, "inv": [], "full_name": fn, "referral": rn, "pending_actions": [], "history": [], "commissions": []}
                update_user(fn, reg[fn]); st.success("Registered! Login now.")

else:
    # --- HOME PAGE ---
    st.markdown("<h1 style='color: #007BFF;'>INTERNATIONAL STOCK MARKET EXCHANGE! 📊📈</h1>", unsafe_allow_html=True)
    st.write("Transform your initial investment into a powerhouse of growth through our precision-engineered market cycles.")
    st.info("### 🚀 Grow your capital by 20% every 7 days!")
    
    col_a, col_b = st.columns([0.1, 0.9])
    with col_a:
        if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    with col_b:
        if st.button("🚀 PRESS HERE TO REGISTER / LOGIN"): 
            st.session_state.page = "login"
            st.rerun()
    
    if st.session_state.admin_mode:
        if st.text_input("code", type="password") == "0102030405": 
            st.session_state.is_boss = True
            st.rerun()
            
