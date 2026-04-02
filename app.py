import streamlit as st
import json
import os
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

# Initialize all variables to prevent crashes
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

# ==========================================
# BLOCK 2: INTERFACE STYLES (UI)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .ad-panel { background: #1c1e26; border-radius: 8px; border: 1px dashed #00eeff; padding: 20px; text-align: center; }
    /* Hidden Admin Button as a Period */
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #8c8f99 !important;
        font-size: 15px !important; padding: 0 !important; margin-left: -5px !important; display: inline !important;
        min-height: 0px !important; width: auto !important;
    }
    .module-card { background: #1a1e26; padding: 15px; border-radius: 10px; border: 1px solid #2d303a; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE 1 - THE ADVERTISEMENT
# ==========================================
if st.session_state.page == "ad" and not st.session_state.user and not st.session_state.is_boss:
    
    # 1. MEGA RAINBOW TITLE
    st.markdown('<h1 style="text-align:center; font-size:45px; font-weight:900; background:linear-gradient(90deg, #ff007f, #ffaa00, #00ff88, #00eeff); -webkit-background-clip: text; color: transparent; margin-bottom:20px;">INTERNATIONAL STOCK MARKET EXCHANGE</h1>', unsafe_allow_html=True)

    # 2. CENTERED BUTTON ROW
    # This creates two columns in the center area
    col_l, col_btn1, col_btn2, col_r = st.columns([0.35, 0.1, 0.2, 0.35])
    
    with col_btn1:
        if st.button("⛔", key="mid_gate_trigger"):
            st.session_state.admin_mode = not st.session_state.admin_mode

    with col_btn2:
        if st.button("🚀 JOIN NOW!", key="jump_to_login"):
            st.session_state.page = "login"
            st.rerun()

    
    # 3. THE ADVERTISEMENT BOX
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

    # SECRET GATE (Appears only after clicking ⛔)
    if st.session_state.admin_mode:
        st.markdown("---")
        code = st.text_input("Security Code", type="password", key="sec_code_input")
        if code == "0102030405":
            st.session_state.is_boss = True
            st.session_state.admin_mode = False
            st.rerun()
            
# --- PAGE 2: ACCESS PORTAL ---
elif st.session_state.page == "login" and not st.session_state.user:
    st.markdown("<h1 style='text-align:center; color:#00eeff;'>ACCESS PORTAL</h1>", unsafe_allow_html=True)
    
    # 1. INITIAL VIEW: ONLY TWO BUTTONS SHOW FIRST
    col_nav1, col_nav2 = st.columns(2)
    
    # Initialize sub_page state to keep inputs hidden initially
    if 'sub_page' not in st.session_state: 
        st.session_state.sub_page = "select"

    with col_nav1:
        if st.button("MEMBER LOG IN", use_container_width=True, key="nav_login"):
            st.session_state.sub_page = "login_form"
    with col_nav2:
        if st.button("REGISTER AS MEMBER", use_container_width=True, key="nav_reg"):
            st.session_state.sub_page = "reg_form"

    st.markdown("---")

    # 2. MEMBER LOG IN SECTION (Appears only after clicking button)
    if st.session_state.sub_page == "login_form":
        st.info("USER NAME: INPUT YOUR 1ST NAME, MIDDLE NAME, AND LAST NAME")
        u_name = st.text_input("FULL USERNAME (ALL CAPS)", key="l_u").upper()
        
        st.info("PASSWORD: INPUT YOUR 6-DIGIT NUMBERS ONLY")
        u_pin = st.text_input("6-DIGIT PIN", type="password", max_chars=6, key="l_p")
        
        if st.button("ENTER DASHBOARD", key="exec_l"):
            reg = load_registry()
            # Remove spaces from input for matching if needed
            formatted_u = u_name.replace(" ", "_")
            if formatted_u in reg and str(reg[formatted_u].get('pin')) == str(u_pin):
                st.session_state.user = formatted_u
                st.rerun()
            else:
                st.error("Invalid Username or 6-Digit PIN")

    # 3. REGISTER AS MEMBER SECTION (Appears only after clicking button)
    elif st.session_state.sub_page == "reg_form":
        st.warning("PLEASE USE CAPSLOCK FOR ALL NAME FIELDS")
        f_name = st.text_input("FIRST NAME", key="reg_f").upper()
        m_name = st.text_input("MIDDLE NAME", key="reg_m").upper()
        l_name = st.text_input("LAST NAME", key="reg_l").upper()
        
        # PIN Constraint
        st.info("PASSWORD MUST BE 6-DIGIT NUMBER!")
        new_pin = st.text_input("CREATE 6-DIGIT PASSCODE", type="password", max_chars=6, key="reg_pin")
        
        # Invitor Section
        st.info("ONLY ACTIVE INVESTOR IS ALLOWED AS INVITOR. IF NONE, TYPE 'DIRECT'")
        inv_input = st.text_input("INVITOR FULL NAME", key="reg_inv").upper()

        # Validation Logic
        reg = load_registry()
        is_valid = False
        if inv_input == "DIRECT":
            is_valid = True
        elif inv_input.strip() != "" and inv_input in reg:
            if len(reg[inv_input].get('inv', [])) > 0:
                is_valid = True

        if is_valid and len(new_pin) == 6 and f_name and l_name:
            if st.button("PROCEED TO ACCOUNT CREATION", key="reg_final", use_container_width=True):
                username = f"{f_name}_{m_name}_{l_name}"
                new_data = {
                    "pin": new_pin,
                    "wallet": 0.0,
                    "inv": [],
                    "full_name": f"{f_name} {m_name} {l_name}",
                    "referred_by": inv_input
                }
                update_user(username, new_data)
                st.success("Account Created! You can now Log In.")
                st.session_state.sub_page = "login_form"

    # Back button to return to Advertisement
    if st.button("← BACK TO ADVERTISEMENT", key="back_to_ad"):
        st.session_state.page = "ad"
        st.session_state.sub_page = "select"
        st.rerun()
        
        

# ==========================================
# BLOCK 6: ADMIN CONTROL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN PANEL")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
        
