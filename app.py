import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# --- 1. DATA PERSISTENCE & REGISTRY ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_to_registry(name, pin):
    registry = load_registry()
    if name in registry:
        return False, "Investor ID already exists. Please Sign In."
    registry[name] = {
        "pin": pin,
        "wallet_balance": 0.0,
        "investments": [],
        "transactions": []
    }
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)
    return True, "Investor ID Created Successfully."

def update_user_data(name, data):
    registry = load_registry()
    registry[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, default=str)

# --- 2. THEMED DESIGN ---
st.set_page_config(page_title="BPSM Official Portal", page_icon="🇵🇭", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    /* The Cover Design */
    .cover-card {
        background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* ================================================
    TARGETED FIX: Visibility Problem for Labels
    ================================================
    Old Style: font-size: 0.7rem; color: #666; font-weight: bold; margin-bottom: -15px;
    ================================================
    */
    .id-label { 
        font-size: 0.8rem; 
        color: #0038a8; /* High Contrast Official Blue */
        font-weight: 900; /* Extra Bold */
        margin-bottom: -15px; 
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8); /* Slight outline for depth */
        font-family: 'Arial Black', sans-serif;
    }
    
    /* Input Form Customization */
    .stTextInput input {
        border-radius: 10px !important;
        border: 2px solid #0038a8 !important;
        height: 3.5rem;
        background-color: #ffffff;
    }
    .stButton>button {
        border-radius: 10px;
        height: 3.5rem;
        font-weight: bold;
        background-color: #0038a8 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION FLOW ---
if 'active_user' not in st.session_state:
    st.session_state.active_user = None

if st.session_state.active_user is None:
    # --- COVER DESIGN ---
    st.markdown("""
        <div class="cover-card">
            <h1 style='margin:0;'>BAGONG PILIPINAS</h1>
            <p style='letter-spacing:3px; opacity:0.9;'>STOCK MARKET PORTAL</p>
            <hr style='opacity:0.3;'>
            <p style='font-size:0.9rem;'>Official Digital Trading Floor</p>
        </div>
        """, unsafe_allow_html=True)

    auth_tab, reg_tab = st.tabs(["🔑 SECURE SIGN-IN", "📝 REGISTER I.D."])

    with auth_tab:
        # These now use the updated .id-label class
        st.markdown("<p class='id-label'>INVESTOR FULL NAME</p>", unsafe_allow_html=True)
        login_name = st.text_input("name_id", label_visibility="collapsed").upper()
        
        st.markdown("<p class='id-label'>6-DIGIT SECURITY PIN</p>", unsafe_allow_html=True)
        login_pin = st.text_input("pin_id", type="password", max_chars=6, label_visibility="collapsed")
        
        if st.button("VERIFY & ENTER PORTAL", use_container_width=True):
            registry = load_registry()
            # Recall saved registration logic
            if login_name in registry and registry[login_name]['pin'] == login_pin:
                st.session_state.active_user = login_name
                st.rerun()
            else:
                st.error("Credential Verification Failed. Check Name or PIN.")

    with reg_tab:
        st.write("### Create Official Investor Account")
        new_name = st.text_input("FULL NAME (AS PER GOVT I.D.)").upper()
        new_pin = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        confirm_pin = st.text_input("CONFIRM PIN", type="password", max_chars=6)
        
        if st.button("REGISTER I.D.", use_container_width=True):
            if len(new_pin) != 6 or not new_pin.isdigit():
                st.error("PIN must be exactly 6 digits (numbers only).")
            elif new_pin != confirm_pin:
                st.error("PINs do not match.")
            elif new_name:
                success, msg = save_user_to_registry(new_name, new_pin)
                if success:
                    st.success("Account created. Please proceed to the Sign-In tab.")
                else:
                    st.warning(msg)

# --- 4. THE DASHBOARD (LOGGED IN) ---
else:
    # (Rest of the program continues unchanged as requested)
    st.write("DASHBOARD PLACEHOLDER - Authenticated as:", st.session_state.active_user)
    if st.button("Logout"):
        st.session_state.active_user = None
        st.rerun()
        
