import streamlit as st
import json
import os
import time  # New import for refresh timing
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: THE CORE ENGINE (DATA & STATE)
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

# Initialize states
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sub_page' not in st.session_state: st.session_state.sub_page = "select"

# --- LIVE REFRESH HEARTBEAT ---
# This makes the numbers tick every second when logged in
if st.session_state.user:
    time.sleep(1)
    st.rerun()

# ==========================================
# BLOCK 2: INTERFACE STYLES (UI)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 20px; text-align: center; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #8c8f99 !important;
        font-size: 15px !important; padding: 0 !important; margin-left: -5px !important; display: inline !important;
        min-height: 0px !important; width: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE 1 - THE ADVERTISEMENT
# ==========================================
if st.session_state.page == "ad" and not st.session_state.user and not st.session_state.is_boss:
    st.markdown('<h1 style="text-align:center; font-size:45px; font-weight:900; background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); -webkit-background-clip: text; color: transparent; margin-bottom:20px;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)

    col_l, col_btn1, col_btn2, col_r = st.columns([0.35, 0.1, 0.2, 0.35])
    with col_btn1:
        if st.button("⛔", key="mid_gate_trigger"):
            st.session_state.admin_mode = not st.session_state.admin_mode
    with col_btn2:
        if st.button("🚀 JOIN NOW!", key="jump_to_login"):
            st.session_state.page = "login"
            st.session_state.sub_page = "select"
            st.rerun()

    st.markdown("""
        <div class="ad-panel" style="margin-top: 15px;">
            <p style="color:#00eeff; font-weight:bold; font-size:18px; margin-bottom:10px; text-align:center;">How We Generate Your Profit:</p>
            <p style="color:#8c8f99; font-size:16px; line-height:1.6; text-align:justify;">
                Your single capital is diversified and cycled multiple times through our advanced AI-managed scalping algorithm every hour. 
                Instead of holding a stock for a year, we take small 0.05% profits from thousands of trades, combining them to provide you 
                with your precise, ticking 20% guaranteed profit over the 7-day cycle. Your money is always moving, never dormant!
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.admin_mode:
        code = st.text_input("Security Code", type="password", key="sec_code_input")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.session_state.admin_mode = False
            st.rerun()

# ==========================================
# BLOCK 4: PAGE 2 - ACCESS PORTAL
# ==========================================
elif st.session_state.page == "login" and not st.session_state.user and not st.session_state.is_boss:
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("MEMBER LOG IN", use_container_width=True):
            st.session_state.sub_page = "login_form"
    with col_nav2:
        if st.button("REGISTER AS MEMBER", use_container_width=True):
            st.session_state.sub_page = "reg_form"

    st.markdown("---")

    # --- MEMBER LOG IN SECTION ---
    if st.session_state.sub_page == "login_form":
        st.info("USER NAME: INPUT YOUR 1ST NAME, MIDDLE NAME, AND LAST NAME")
        u_name_in = st.text_input("FULL USERNAME", key="l_u").upper().strip()
        
        st.info("PASSWORD: INPUT YOUR 6-DIGIT NUMBERS")
        u_pin = st.text_input("6-DIGIT PIN", type="password", max_chars=6, key="l_p")
        
        # Physical Button to Enter
        if st.button("LOG IN NOW", key="btn_login_final", use_container_width=True):
            reg = load_registry()
            formatted_underscore = u_name_in.replace(" ", "_")
            user_data = reg.get(u_name_in) or reg.get(formatted_underscore)
            
            if user_data and str(user_data.get('pin')) == str(u_pin):
                st.session_state.user = u_name_in if u_name_in in reg else formatted_underscore
                st.rerun()
            else:
                st.error("Invalid Username or PIN.")

    # --- REGISTER AS MEMBER SECTION ---
    elif st.session_state.sub_page == "reg_form":
        st.warning("PLEASE USE CAPSLOCK FOR ALL NAME FIELDS")
        f_name = st.text_input("FIRST NAME", key="reg_f").upper().strip()
        m_name = st.text_input("MIDDLE NAME", key="reg_m").upper().strip()
        l_name = st.text_input("LAST NAME", key="reg_l").upper().strip()
        
        # Double Confirmation for Passcode
        st.info("CREATE YOUR 6-DIGIT PASSCODE")
        pass1 = st.text_input("ENTER 6-DIGIT PASSCODE", type="password", max_chars=6, key="p1")
        pass2 = st.text_input("CONFIRM 6-DIGIT PASSCODE", type="password", max_chars=6, key="p2")
        
        st.info("INVITOR: TYPE FULL NAME OR 'DIRECT'")
        inv_input = st.text_input("INVITOR FULL NAME", key="reg_inv").upper().strip()

        # Validation Logic
        reg = load_registry()
        is_valid_inv = False
        if inv_input == "DIRECT": 
            is_valid_inv = True
        elif inv_input != "":
            inv_alt = inv_input.replace(" ", "_")
            if inv_input in reg or inv_alt in reg:
                inv_key = inv_input if inv_input in reg else inv_alt
                if len(reg[inv_key].get('inv', [])) > 0:
                    is_valid_inv = True

        # Check if passwords match before showing the button
        if pass1 != pass2 and len(pass2) == 6:
            st.error("❌ PASSCODES DO NOT MATCH!")
        
        # PROCEED only if all conditions met + Passwords Match
        if is_valid_inv and len(pass1) == 6 and pass1 == pass2 and f_name and l_name:
            st.success("✅ Information Verified. You may now create your account.")
            if st.button("PROCEED TO ACCOUNT CREATION", key="reg_btn_final", use_container_width=True):
                db_key = f"{f_name}_{m_name}_{l_name}"
                update_user(db_key, {
                    "pin": pass1, 
                    "wallet": 0.0, 
                    "inv": [], 
                    "full_name": f"{f_name} {m_name} {l_name}", 
                    "referred_by": inv_input
                })
                st.success("Registration Successful!")
                st.session_state.sub_page = "login_form"
        

# ==========================================
# BLOCK 5: THE USER DASHBOARD (LIVE VERSION)
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    
    # Header
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(f"### BPSM\nWelcome, {data.get('full_name', 'User')}")
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    # Balance Display
    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #2d303a;">
            <p style="color:#8c8f99; font-size:14px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data.get('wallet', 0):,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.button("📥 Deposit", use_container_width=True)
    c2.button("💸 Withdraw", use_container_width=True)
    c3.button("♻️ Reinvest", use_container_width=True)
# ==========================================
# BLOCK 4: PAGE 2 - ACCESS PORTAL
# ==========================================
elif st.session_state.page == "login" and not st.session_state.user and not st.session_state.is_boss:
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("MEMBER LOG IN", use_container_width=True):
            st.session_state.sub_page = "login_form"
    with col_nav2:
        if st.button("REGISTER AS MEMBER", use_container_width=True):
            st.session_state.sub_page = "reg_form"

    st.markdown("---")

    if st.session_state.sub_page == "login_form":
        st.info("USER NAME: INPUT YOUR 1ST NAME, MIDDLE NAME, AND LAST NAME")
        # .strip() removes accidental extra spaces at the start or end
        u_name_in = st.text_input("FULL USERNAME (ALL CAPS)", key="l_u").upper().strip()
        
        st.info("PASSWORD: INPUT YOUR 6-DIGIT NUMBERS ONLY")
        u_pin = st.text_input("6-DIGIT PIN", type="password", max_chars=6, key="l_p")
        
        if st.button("ENTER DASHBOARD"):
            reg = load_registry()
            # FIX: Convert spaces to underscores to match the registration format
            formatted_name = u_name_in.replace(" ", "_")
            
            # Check both the typed version and the underscore version
            user_data = reg.get(u_name_in) or reg.get(formatted_name)
            
            if user_data and str(user_data.get('pin')) == str(u_pin):
                st.session_state.user = u_name_in if u_name_in in reg else formatted_name
                st.success("Login Successful!")
                st.rerun()
            else: 
                # This error shows if the name or PIN is wrong
                st.error("Invalid Username or 6-Digit PIN")

    elif st.session_state.sub_page == "reg_form":
        st.warning("PLEASE USE CAPSLOCK FOR ALL NAME FIELDS")
        f_name = st.text_input("FIRST NAME", key="reg_f").upper().strip()
        m_name = st.text_input("MIDDLE NAME", key="reg_m").upper().strip()
        l_name = st.text_input("LAST NAME", key="reg_l").upper().strip()
        
        st.info("PASSWORD MUST BE 6-DIGIT NUMBER!")
        new_pin = st.text_input("CREATE 6-DIGIT PASSCODE", type="password", max_chars=6, key="reg_pin")
        
        st.info("ONLY ACTIVE INVESTOR IS ALLOWED AS INVITOR. IF NONE, TYPE 'DIRECT'")
        inv_input = st.text_input("INVITOR FULL NAME", key="reg_inv").upper().strip()

        reg = load_registry()
        is_valid = False
        if inv_input == "DIRECT": 
            is_valid = True
        elif inv_input != "" and (inv_input in reg or inv_input.replace(" ", "_") in reg):
            check_name = inv_input if inv_input in reg else inv_input.replace(" ", "_")
            # Only allow if they have an active cycle
            if len(reg[check_name].get('inv', [])) > 0: 
                is_valid = True
                st.success(f"Verified Invitor: {check_name}")

        if is_valid and len(new_pin) == 6 and f_name and l_name:
            if st.button("PROCEED TO ACCOUNT CREATION", use_container_width=True):
                # We save with underscores to keep the database organized
                db_username = f"{f_name}_{m_name}_{l_name}"
                update_user(db_username, {
                    "pin": new_pin, 
                    "wallet": 0.0, 
                    "inv": [], 
                    "full_name": f"{f_name} {m_name} {l_name}", 
                    "referred_by": inv_input
                })
                st.success("Account Created! You can now Log In.")
                st.session_state.sub_page = "login_form"

# ==========================================
# BLOCK 5: THE USER DASHBOARD (LIVE VERSION)
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    
    # Header with BPSM Title
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown(f"### BPSM")
        st.markdown(f"<p style='color:#8c8f99;'>Welcome, {data.get('full_name', 'User')}</p>", unsafe_allow_html=True)
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    # Withdrawable Balance
    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #2d303a;">
            <p style="color:#8c8f99; font-size:14px; letter-spacing:1px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data.get('wallet', 0):,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action Buttons
    c1, c2, c3 = st.columns(3)
    c1.button("📥 Deposit", use_container_width=True)
    c2.button("💸 Withdraw", use_container_width=True)
    c3.button("♻️ Reinvest", use_container_width=True)

    # Active Cycles with Live Ticking ROI
    st.markdown('<p style="background:#2d303a; padding:5px 15px; border-left: 5px solid #ff4b4b; font-weight:bold;">⌛ ACTIVE CYCLES</p>', unsafe_allow_html=True)
    
    # If no cycles, display info
    if not data.get('inv'):
        st.info("No active cycles found. Visit the Admin Panel to add a deposit.")
    
    for inv in data.get('inv', []):
        # Time logic: 7 Day Cycle
        start_time = datetime.fromisoformat(inv['start_time'])
        end_time = start_time + timedelta(days=7)
        now = datetime.now()
        remaining = end_time - now
        
        if remaining.total_seconds() > 0:
            # ROI Math: 20% over 7 days
            elapsed = (now - start_time).total_seconds()
            total_sec = 7 * 24 * 3600
            current_roi = (inv['amount'] * 0.20) * (elapsed / total_sec)
            
            d = remaining.days
            h, rem = divmod(remaining.seconds, 3600)
            m, s = divmod(rem, 60)
            
            st.markdown(f"""
                <div style="background:#16191f; border-left: 4px solid #00ff88; padding:15px; border-radius:5px; margin-bottom:10px; border: 1px solid #2d303a;">
                    <p style="margin:0; color:white; font-size:16px;">Capital: <b>₱{inv['amount']:,.1f}</b></p>
                    <p style="color:#00ff88; font-size:11px; margin:5px 0 0 0; letter-spacing:1px;">ACCUMULATED ROI:</p>
                    <h2 style="color:#00ff88; margin:0; font-family:monospace;">₱{current_roi:,.4f}</h2>
                    <p style="color:#8c8f99; font-size:13px;">Total to Receive: ₱{inv['amount']*1.2:,.2f}</p>
                    <p style="color:#ff4b4b; font-weight:bold; margin-top:10px; font-size:15px;">⌛ TIME REMAINING: {d}D {h}H {m}M {s}S</p>
                    <div style="background:#262730; color:#8c8f99; text-align:center; padding:5px; font-size:11px; margin-top:10px; border-radius:3px;">
                        AVAILABLE TO PULL OUT FROM {end_time.strftime('%b %d, %I:%M %p').upper()}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    

# ==========================================
# BLOCK 6: ADMIN PANEL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN PANEL")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
                                          
