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
            

# ==========================================
# BLOCK 6: ADMIN CONTROL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN PANEL")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
        
