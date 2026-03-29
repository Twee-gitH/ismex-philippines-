import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import random

# --- 1. DATA PERSISTENCE & REGISTRY (UNTOUCHED LOGIC) ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_to_registry(name, pin):
    registry = load_registry()
    if name in registry:
        return False, "Investor I.D. already exists."
    registry[name] = {
        "pin": pin,
        "wallet_balance": 0.0,
        "investments": [],
        "transactions": []
    }
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)
    return True, "Investor I.D. Created Successfully."

def update_user_data(name, data):
    registry = load_registry()
    registry[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)

# --- 2. THEMED DESIGN (THE RADICAL FACE-LIFT) ---
# This style block mimics the dark theme, neon green, and card layout of your photo.
st.set_page_config(page_title="BPSM Official Portal", page_icon="🇵🇭", layout="centered")

st.markdown("""
    <style>
    /* Dark Theme Foundation */
    .stApp { background-color: #0b0c0e; color: white; }
    header, [data-testid="stHeader"] { background-color: transparent !important; }
    
    /* Top Logo Header (Matching the 'RISCOIN' style) */
    .top-brand {
        text-align: center;
        color: #ffffff;
        font-family: 'Arial Black', sans-serif;
        font-size: 2rem;
        letter-spacing: 2px;
        margin-top: 10px;
        margin-bottom: 5px;
        text-shadow: 0 0 10px rgba(0, 56, 168, 0.3);
    }
    .top-sub-brand {
        text-align: center;
        color: #ce1126; /* Official Red */
        font-size: 0.8rem;
        letter-spacing: 3px;
        margin-top: -10px;
        margin-bottom: 30px;
    }

    /* The "Quick Trade" Green Card */
    .trade-card {
        background-color: #0dcf70;
        padding: 20px;
        border-radius: 15px;
        color: #0b0c0e;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 5px 15px rgba(13, 207, 112, 0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Market Overview Mini-Graphs Card */
    .market-overview-card {
        background-color: #17181c;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2a2b30;
        margin-bottom: 15px;
    }
    .overview-pair { color: #8c8f99; font-size: 0.8rem; }
    .overview-price { color: white; font-size: 1.1rem; font-weight: bold; }
    .overview-change { color: #0dcf70; font-weight: bold; }

    /* Custom Labels */
    .id-label { 
        font-size: 0.85rem; 
        color: #8c8f99;
        font-weight: 900; 
        margin-bottom: 0.4rem;
        font-family: 'Arial Black', sans-serif;
        display: block;
        text-transform: uppercase;
    }

    /* Standardized Input Customization */
    .stTextInput input, .stNumberInput input {
        border-radius: 12px !important;
        border: 2px solid #2a2b30 !important;
        height: 4rem !important; 
        font-size: 1.2rem !important; 
        background-color: #17181c !important;
        color: white !important;
        padding: 12px !important;
    }
    .stTextInput input:focus { border-color: #0038a8 !important; }

    /* Button Style (Pulsing Glow from your photo) */
    .stButton>button {
        border-radius: 12px;
        height: 4rem;
        font-size: 1.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0dcf70 0%, #066637 100%) !important;
        color: #0b0c0e !important;
        border: none !important;
        box-shadow: 0 5px 20px rgba(13, 207, 112, 0.3);
        margin-top: 10px;
    }

    /* Tab Layout Fix */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #8c8f99; font-weight: bold; font-size: 1rem; border-radius: 10px; padding: 10px 20px; }
    .stTabs [data-baseweb="tab"]:hover { color: #ffffff; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #0dcf70 !important; border-bottom-color: #0dcf70 !important; }

    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION FLOW (UNTOUCHED LOGIC) ---
if 'active_user' not in st.session_state:
    st.session_state.active_user = None

if st.session_state.active_user is None:
    # Top BPSM Header in RISCOIN Style
    st.markdown("<h1 class='top-brand'>BPSM</h1>", unsafe_allow_html=True)
    st.markdown("<p class='top-sub-brand'>BAGONG PILIPINAS STOCK MARKET</p>", unsafe_allow_html=True)
    
    # Custom Green Card as the Sign-In Hub
    st.markdown("""
        <div class="trade-card">
            <div>
                <b>Start Trading Today</b><br>
                Official Digital Floor
            </div>
            <div style="font-size: 2rem;">👤</div>
        </div>
        """, unsafe_allow_html=True)

    # Login and Registration Tabs using New Style
    auth_tab, reg_tab = st.tabs(["🔑 SIGN IN", "📝 REGISTER"])

    with auth_tab:
        st.markdown("<p class='id-label'>INVESTOR FULL NAME</p>", unsafe_allow_html=True)
        login_name = st.text_input("name_id", placeholder="name_id", label_visibility="collapsed").upper()
        
        st.markdown("<p class='id-label'>6-DIGIT SECURITY PIN</p>", unsafe_allow_html=True)
        login_pin = st.text_input("pin_id", type="password", max_chars=6, placeholder="pin_id", label_visibility="collapsed")
        
        if st.button("VERIFY & ENTER PORTAL", use_container_width=True):
            registry = load_registry()
            # Verification logic stays identical
            if login_name in registry and registry[login_name]['pin'] == login_pin:
                st.session_state.active_user = login_name
                st.rerun()
            else:
                st.error("Credential Verification Failed. Check Name or PIN.")

    with reg_tab:
        st.write("### Create Official Investor ID")
        new_name = st.text_input("FULL NAME (AS PER GOVT I.D.)").upper()
        new_pin = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        confirm_pin = st.text_input("CONFIRM PIN", type="password", max_chars=6)
        
        if st.button("REGISTER I.D.", use_container_width=True):
            if len(new_pin) != 6 or not new_pin.isdigit():
                st.error("PIN must be exactly 6 digits.")
            elif new_pin != confirm_pin:
                st.error("PINs do not match.")
            elif new_name:
                success, msg = save_user_to_registry(new_name, new_pin)
                if success:
                    st.success("Account Created! You can now Sign In.")
                else:
                    st.warning(msg)

# --- 4. THE DASHBOARD (NEW MODERN FINTECH LOOK) ---
else:
    current_username = st.session_state.active_user
    registry = load_registry()
    user_data = registry[current_username]

    # Matching the Top Bar
    st.markdown("<h1 class='top-brand' style='font-size: 1.5rem;'>BPSM PORTAL</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>Investor: <b>{current_username}</b></p>", unsafe_allow_html=True)
    
    # Matching the "Market Overview" Card from photo
    # This simulates market data to complete the look.
    st.markdown("""
        <div class="market-overview-card">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span class="overview-pair">BPSM/PHP</span><br>
                    <span class="overview-price">₱66,559.64</span>
                    <span class="overview-change">+0.01%</span>
                </div>
                <div style="font-size: 1.5rem;">📈</div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <div>
                    <span class="overview-pair">MNL/USD</span><br>
                    <span class="overview-price">$1998.52</span>
                    <span class="overview-change">+0.03%</span>
                </div>
                <div>
                    <span class="overview-pair">TRX/USDT</span><br>
                    <span class="overview-price">0.31966</span>
                    <span class="overview-change">+0.08%</span>
                </div>
            </div>
        </div>
        """,
    
