import streamlit as st
import json
import os
import shutil
from datetime import datetime, timedelta
import time
import pandas as pd

# --- 1. SESSION INITIALIZER ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if not os.path.exists("receipts"):
    os.makedirs("receipts")

# --- 2. DATA ENGINE ---
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

# --- 3. UI STYLING ---
st.set_page_config(page_title="BPSM Official", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    .stApp { background-color: #0b0c0e; color: white; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .user-box { text-align: center; padding: 30px 10px; background: #111217; border-bottom: 1px solid #2a2b30; }
    .balance-val { color: #0dcf70; font-size: 3.5rem; font-weight: 900; margin: 5px 0; }
    .section-header { background: #1c1e24; padding: 12px 20px; margin-top: 25px; border-left: 5px solid #0dcf70; font-weight: bold; text-transform: uppercase; color: #0dcf70; }
    .roi-text { color: #0dcf70; font-weight: bold; font-size: 1.1rem; }
    .meta-text { color: #8c8f99; font-size: 0.85rem; margin-bottom: 2px; }
    .timer-alert { color: #ff4b4b; font-weight: bold; font-size: 1.2rem; text-align: center; }
    .stButton>button { border-radius: 12px !important; height: 3.5rem !important; font-weight: bold !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME", key="login_name").upper()
        lp = st.text_input("SECURE PIN", type="password", max_chars=6, key="login_pin")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln].get('pin') == lp:
                st.session_state.user = ln
                st.rerun()
            elif ln == "ADMIN" and lp == "000000": # Admin Shortcut
                st.session_state.is_boss = True
                st.rerun()
            else: st.error("Invalid Credentials")
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6, key="reg_pin")
        referrer = st.text_input("REFERRER NAME (REQUIRED)", key="reg_ref").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if not referrer or (referrer != "DIRECT" and referrer not in reg): 
                st.error("Valid Referrer required. (Type DIRECT if none)")
            elif rn in reg: st.error("Already registered.")
            elif rn and len(rp) == 6:
                update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer, "bonus_claimed": False})
                st.success("Account Created!"); time.sleep(1.5); st.rerun()
    st.stop()

# --- 5. INVESTOR PORTAL ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # --- AUTO-PROCESSOR (ROI & RENEWAL) ---
    data_changed = False
    for i in data.get('inv', []):
        try:
            m_time = datetime.fromisoformat(i['end'])
            if now >= m_time and not i.get('roi_paid', False):
                profit = i['amt'] * 0.20
                data['wallet'] += profit
                i['roi_paid'] = True
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI CREDIT", "amt": profit, "status": "SUCCESSFUL"})
                data_changed = True
            
            if now >= (m_time + timedelta(hours=1)):
                i['start'] = now.isoformat()
                i['end'] = (now + timedelta(days=7)).isoformat()
                i['roi_paid'] = False 
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "AUTO-RENEWAL (7 DAYS)", "amt": i['amt'], "status": "SUCCESSFUL"})
                data_changed = True
        except: continue
    
    if data_changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>WITHDRAWABLE BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

    # --- NAVIGATION ---
    if st.session_state.page == "dep":
        st.markdown("<div class='section-header'>📥 DEPOSIT</div>", unsafe_allow_html=True)
        d_amt = st.number_input("Amount", min_value=1000.0)
        receipt = st.file_uploader("Receipt", type=['jpg','png'])
        if st.button("SUBMIT"):
            if receipt:
                f_path = f"receipts/{name}_{int(time.time())}.png"
                with open(f_path, "wb") as f: f.write(receipt.getbuffer())
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": d_amt, "status": "PENDING_DEP", "receipt_path": f_path})
                update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    elif st.session_state.page == "wd":
        st.markdown("<div class='section-header'>📤 WITHDRAW</div>", unsafe_allow_html=True)
        w_amt = st.number_input("Amount", min_value=1000.0, max_value=max(1000.0, data['wallet']))
        if st.button("SUBMIT"):
            data['wallet'] -= w_amt
            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WITHDRAWAL", "amt": w_amt, "status": "PENDING_WD"})
            update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    elif st.session_state.page == "reinvest":
        st.markdown("<div class='section-header'>♻️ RE-INVEST</div>", unsafe_allow_html=True)
        r_amt = st.number_input("Re-invest Amount", min_value=1000.0, max_value=max(1000.0, data['wallet']))
        if st.button("START CYCLE"):
            data['wallet'] -= r_amt
            st_t = datetime.now()
            data.setdefault('inv', []).append({"amt": r_amt, "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat(), "roi_paid": False})
            data.setdefault('tx', []).append({"date": st_t.strftime("%Y-%m-%d %H:%M"), "type": "RE-INVESTMENT", "amt": r_amt, "status": "SUCCESSFUL"})
            update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    else:
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        with c2: 
            if st.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()
        with c3:
            if st.button("♻️ RE-INVEST"): st.session_state.page = "reinvest"; st.rerun()

        # Active Cycles
        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
        if not data.get('inv'): st.write("No active interest running.")
        else:
            for idx, t in enumerate(reversed(data['inv'])):
                actual_idx = len(data['inv']) - 1 - idx
                start_t, end_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
                st.markdown(f"<div style='background:#1c1e24; padding:15px; border-radius:15px; border:1px solid #3a3d46; margin-bottom:10px;'><div class='meta-text'>📅 DEPOSIT: {start_t.strftime('%Y-%m-%d %I:%M %p')}</div><div class='meta-text'>🏁 MATURITY: {end_t.strftime('%Y-%m-%d %I:%M %p')}</div><div style='display:flex; justify-content:space-between; margin-top:5px;'><span style='font-weight:bold;'>Capital: ₱{t['amt']:,}</span><span class='roi-text'>TOTAL ROI: ₱{t['amt']*0.20:,.2f}</span></div></div>", unsafe_allow_html=True)
                
                if now < end_t:
                    st.button(f"LOCKED (⏳ {str(end_t - now).split('.')[0]})", key=f"l_{actual_idx}", disabled=True)
                elif end_t <= now < (end_t + timedelta(hours=1)):
                    if st.button(f"✅ PULL CAPITAL (₱{t['amt']:,})", key=f"pull_{actual_idx}"):
                        data['wallet'] += t['amt']
                        data['inv'].pop(actual_idx)
                        data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "CAPITAL PULL-OUT", "amt": t['amt'], "status": "SUCCESSFUL"})
                        update_user(name, data); st.rerun()

        # --- RESTORED REFERRAL SECTION ---
        st.markdown("<div class='section-header'>👥 MY REFERRALS</div>", unsafe_allow_html=True)
        all_users = load_registry()
        # Find anyone who has this user's name as their 'ref_by'
        my_referrals = [{"INVITEE": u, "CAPITAL": sum([i['amt'] for i in info.get('inv', [])])} 
                        for u, info in all_users.items() if info.get('ref_by') == name]
        
        if my_referrals:
            ref_df = pd.DataFrame(my_referrals)
            st.table(ref_df)
            total_ref_cap = sum([r['CAPITAL'] for r in my_referrals])
            st.write(f"**Commission Earned (5%):** ₱{total_ref_cap * 0.05:,.2f}")
        else:
            st.info("No successful referrals yet.")

        # History
        st.markdown("<div class='section-header'>📜 HISTORY</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"{t['date']} | {t['type']} | ₱{t['amt']:,} | {t['status']}")

    if st.sidebar.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    all_users = load_registry()
    st.markdown("### 👑 MASTER CONTROL")
    st.markdown("<div class='section-header'>📋 INVESTOR DATABASE</div>", unsafe_allow_html=True)
    db = [{"NAME": u, "PIN": i.get('pin'), "WALLET": f"₱{i.get('wallet',0):,.2f}", "REFERRER": i.get('ref_by','DIRECT')} for u,i in all_users.items()]
    st.table(pd.DataFrame(db))

    st.markdown("<div class='section-header'>🔔 PENDING ACTIONS</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']:,} Deposit: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_DEP"
                    st_t = datetime.now()
                    all_users[u_name].setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(u_name, all_users[u_name]); st.rerun()
            elif tx['status'] == "PENDING_WD":
                if st.button(f"Approve ₱{tx['amt']:,} Withdrawal: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_WD"
                    update_user(u_name, all_users[u_name]); st.rerun()
    
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
