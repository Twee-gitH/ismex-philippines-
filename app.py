import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

# --- 1. DATA & REGISTRY ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)

# --- 2. THE ULTIMATE MOBILE FIT (FIXES SCREEN WIDTH) ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    </head>
    <style>
    /* Force the content to take up 100% of the phone screen */
    .block-container {
        padding: 1rem !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }
    
    /* Hide the huge sidebar and top padding */
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    .stApp { background-color: #0b0c0e; color: white; }
    
    /* BIG LABELS & BLACK TEXT ON WHITE BOXES */
    .id-label { font-size: 1rem; color: #8c8f99; font-weight: bold; margin-bottom: 5px; }
    .stTextInput input, .stNumberInput input {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important;
        border-radius: 12px !important;
        height: 4rem !important;
        font-size: 18px !important; /* Prevents auto-zoom on iPhone */
        font-weight: bold !important;
    }

    /* NEON GREEN BUTTONS - BIG FOR FINGERS */
    .stButton>button {
        width: 100% !important;
        height: 4.5rem !important;
        border-radius: 15px !important;
        background: #0dcf70 !important;
        color: #0b0c0e !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(13, 207, 112, 0.4);
    }

    /* MARKET CARDS */
    .trade-card {
        background-color: #17181c; padding: 15px; border-radius: 15px;
        border: 1px solid #2a2b30; margin-bottom: 12px; width: 100%;
    }
    .timer-text { color: #0dcf70; font-family: monospace; font-size: 1.2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DASHBOARD LOGIC ---
if 'user' not in st.session_state: st.session_state.user = "AGTA AGATA" # Hardcoded for test based on your screen

name = st.session_state.user
reg = load_registry()

# Create test data if registry is empty
if name not in reg:
    reg[name] = {"wallet": 0.0, "inv": [], "tx": []}

data = reg[name]
now = datetime.now()

# Calculate Profits
matured = 0
active_trades = []
for i in data['inv']:
    if now >= datetime.fromisoformat(i['end']): matured += (i['amt'] + i['prof'])
    else: active_trades.append(i)

if matured > 0:
    data['wallet'] += matured
    data['inv'] = active_trades
    update_user(name, data)

# --- THE USER INTERFACE ---
st.markdown(f"<h1 style='text-align:center; color:white;'>{name}</h1>", unsafe_allow_html=True)

st.markdown("""
    <div style="background: #17181c; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #2a2b30;">
        <p style="color: #8c8f99; margin: 0;">AVAILABLE BALANCE</p>
        <h1 style="color: #0dcf70; margin: 0; font-size: 2.5rem;">₱{:,.2f}</h1>
    </div>
""".format(data['wallet']), unsafe_allow_html=True)

tab_inv, tab_wall, tab_act = st.tabs(["🚀 INVEST", "💳 WALLET", "📋 ACTIVE"])

with tab_inv:
    st.markdown("<p class='id-label'>INVESTMENT AMOUNT (10% PROFIT)</p>", unsafe_allow_html=True)
    amt = st.number_input("n_amt", min_value=100.0, step=100.0, label_visibility="collapsed")
    if st.button("CONFIRM INVESTMENT"):
        if data['wallet'] >= amt:
            data['wallet'] -= amt
            end_t = (now + timedelta(hours=24)).isoformat()
            data['inv'].append({"amt": amt, "prof": amt*0.1, "end": end_t})
            update_user(name, data)
            st.rerun()
        else: st.error("Low Balance")

with tab_wall:
    action = st.radio("Choose Action", ["Deposit", "Withdraw"], horizontal=True)
    if action == "Deposit":
        st.write("Send GCash to: **0912-345-6789**")
        d_amt = st.number_input("Amount Sent", min_value=100.0)
        ref = st.text_input("Ref Number")
        if st.button("SUBMIT REPORT"):
            data['tx'].append({"type": "DEP", "amt": d_amt, "ref": ref, "status": "PENDING"})
            update_user(name, data)
            st.success("Reported!")
    else:
        w_amt = st.number_input("Amount to Withdraw", min_value=100.0)
        if st.button("REQUEST PAYOUT"):
            if data['wallet'] >= w_amt:
                data['wallet'] -= w_amt
                data['tx'].append({"type": "WD", "amt": w_amt, "status": "PENDING"})
                update_user(name, data)
                st.warning("Request Sent.")

with tab_act:
    if not active_trades:
        st.write("No active trades.")
    for t in active_trades:
        rem = datetime.fromisoformat(t['end']) - now
        time_str = str(rem).split(".")[0]
        st.markdown(f"""
            <div class="trade-card">
                <b>Amount:</b> ₱{t['amt']:,} <br>
                <b>Profit:</b> <span style="color:#0dcf70;">+₱{t['prof']:,}</span> <br>
                <b>Timer:</b> <span class="timer-text">{time_str}</span>
            </div>
        """, unsafe_allow_html=True)

st.button("LOGOUT", on_click=lambda: st.session_state.update({"user": None}))
time.sleep(5)
st.rerun()
