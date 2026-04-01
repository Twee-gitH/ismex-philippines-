import streamlit as st
import json
import os
import shutil
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. INITIAL SETUP ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if not os.path.exists("receipts"):
    os.makedirs("receipts")

# --- 2. DATA HANDLER ---
REGISTRY_FILE = "bpsm_registry.json"
BACKUP_FILE = "bpsm_backup.json"

def load_registry():
    for file in [REGISTRY_FILE, BACKUP_FILE]:
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except: continue
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)
    shutil.copy(REGISTRY_FILE, BACKUP_FILE)

# --- 3. THE STYLE FIX (PIN Case-Sensitivity) ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    input[type="password"] { text-transform: none !important; -webkit-text-transform: none !important; }
    .user-box { background-color: #1c1e24; padding: 20px; border-radius: 15px; border: 1px solid #3a3d46; text-align: center; margin-bottom: 20px; }
    .balance-val { color: #00ff88; font-size: 36px; margin: 0; }
    .section-header { background: #252830; padding: 10px; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #ce1126; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1></div>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME", key="login_name").upper()
        lp = st.text_input("SECURE PIN", type="password", key="login_pin")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln].get('pin') == lp:
                st.session_state.user = ln
                st.rerun()
            else: st.error("❌ INVALID CREDENTIALS")
            
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp1 = st.text_input("CREATE PIN", type="password", key="reg_pin1")
        rp2 = st.text_input("CONFIRM PIN", type="password", key="reg_pin2")
        referrer = st.text_input("REFERRER NAME", key="reg_ref").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if len(rn.split()) < 2: st.error("❌ USE FULL NAME.")
            elif rp1 != rp2: st.error("❌ PIN MISMATCH.")
            elif not referrer or referrer not in reg: st.error("❌ INVALID REFERRER.")
            else:
                update_user(rn.upper(), {"pin": rp1, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer, "claimed_refs": []})
                st.success("✅ REGISTERED!"); time.sleep(1); st.rerun()

    with st.expander("🔐 ADMIN"):
        ap = st.text_input("ADMIN PIN", type="password")
        if st.button("LOG IN AS BOSS"):
            if ap == "Admin123": # <--- Change this to your PIN
                st.session_state.is_boss = True
                st.rerun()
            else: st.error("❌ UNAUTHORIZED")
    st.stop()

# --- 5. INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # ORIGINAL 20% WEEKLY ROI LOGIC
    changed = False
    for i in data.get('inv', []):
        try:
            m_time = datetime.fromisoformat(i['end'])
            if now >= m_time and not i.get('roi_paid', False):
                data['wallet'] += i['amt'] * 0.20
                i['roi_paid'] = True
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI", "amt": i['amt']*0.20, "status": "SUCCESSFUL"})
                changed = True
        except: continue
    if changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p>BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1></div>", unsafe_allow_html=True)

    # ORIGINAL BUTTONS
    if st.session_state.page == "main":
        c1, c2, c3 = st.columns(3)
        if c1.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        if c2.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()
        if c3.button("♻️ RE-INVEST"): st.session_state.page = "rei"; st.rerun()

        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
        for idx, t in enumerate(data.get('inv', [])):
            st.write(f"Capital: ₱{t['amt']:,} | Ends: {t['end'][:16]}")

        st.markdown("<div class='section-header'>👥 REFERRALS</div>", unsafe_allow_html=True)
        st.write(f"Invited By: {data.get('ref_by', 'NONE')}")
        # Your original simple referral table logic
        refs = [u for u, d in reg.items() if d.get('ref_by') == name]
        if refs: st.write(", ".join(refs))

    elif st.session_state.page == "dep":
        amt = st.number_input("Deposit Amount", 1000.0)
        if st.button("SUBMIT DEPOSIT"):
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": amt, "status": "PENDING_DEP"})
            update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("BACK"): st.session_state.page = "main"; st.rerun()

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    st.title("👑 BOSS CONTROL")
    # Simple original approval logic
    all_reg = load_registry()
    for u, d in all_reg.items():
        for idx, tx in enumerate(d.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']} for {u}"):
                    d['tx'][idx]['status'] = "SUCCESSFUL"
                    d.setdefault('inv', []).append({"amt": tx['amt'], "end": (datetime.now()+timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(u, d); st.rerun()
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
        
