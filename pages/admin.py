import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import random
import pandas as pd

# --- 1. SESSION INITIALIZER ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "main"
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

# --- 2. DATA & SYSTEM ENGINES ---
REGISTRY_FILE = "bpsm_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, default=str)

def get_status_msg():
    if os.path.exists("status.txt"):
        with open("status.txt", "r") as f: return f.read()
    return "Market cycles are currently STABLE."

def set_status_msg(msg):
    with open("status.txt", "w") as f: f.write(msg)

def is_maintenance_on():
    if os.path.exists("maint.txt"):
        with open("maint.txt", "r") as f: return f.read() == "ON"
    return False

def set_maintenance(state):
    with open("maint.txt", "w") as f: f.write("ON" if state else "OFF")

def get_wd_fee():
    if os.path.exists("fee.txt"):
        try: return float(open("fee.txt", "r").read())
        except: return 2.0
    return 2.0

def set_wd_fee(val):
    with open("fee.txt", "w") as f: f.write(str(val))

# --- 3. PREMIUM MOBILE UI ---
st.set_page_config(page_title="BPSM Official", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    .stApp { background-color: #0b0c0e; color: white; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .banner { background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center; border-bottom: 5px solid #0dcf70; }
    .banner h1 { font-family: 'Arial Black'; font-size: 2.2rem; color: white; margin: 0; line-height: 1.1; text-shadow: 2px 2px #000; }
    .banner p { font-size: 0.95rem; color: #ffffff; margin-top: 15px; font-weight: 600; line-height: 1.5; }
    .user-box { text-align: center; padding: 30px 10px; background: #111217; border-bottom: 1px solid #2a2b30; }
    .balance-val { color: #0dcf70; font-size: 3.5rem; font-weight: 900; margin: 5px 0; }
    .news-card { background: #1c1e24; border: 1px solid #0038a8; padding: 15px; border-radius: 15px; margin: 15px; border-left: 5px solid #0038a8; font-size: 0.9rem; }
    .section-header { background: #1c1e24; padding: 12px 20px; margin-top: 25px; border-left: 5px solid #0dcf70; font-weight: bold; font-size: 1.1rem; text-transform: uppercase; color: #0dcf70; }
    .stButton>button { width: 100% !important; border-radius: 15px !important; height: 4.5rem !important; background: #1c1e24 !important; color: #ffffff !important; border: 1px solid #3a3d46 !important; font-weight: bold !important; }
    div[data-testid="stButton"] > button:contains("DEPLOY") { background: #0dcf70 !important; color: #0b0c0e !important; font-size: 1.3rem !important; font-weight: 900 !important; border: none !important; }
    .ticker-wrap { background: #000; color: #0dcf70; padding: 12px 0; position: fixed; bottom: 0; width: 100%; font-size: 0.85rem; border-top: 1px solid #2a2b30; font-weight: bold; z-index: 999; }
    .stNumberInput input { color: #000 !important; background-color: #fff !important; height: 3.8rem !important; font-size: 18px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None:
    st.markdown("""<div class="banner"><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1><p>By pooling capital, we acquire essential goods at wholesale prices... Your investment is backed by high-demand physical commodities.</p></div>""", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME").upper()
        lp = st.text_input("SECURE PIN", type="password", max_chars=6)
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and reg[ln]['pin'] == lp:
                st.session_state.user = ln
                st.rerun()
    with t2:
        rn = st.text_input("FULL LEGAL NAME").upper()
        rp = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
        if st.button("CREATE ACCOUNT"):
            if rn and len(rp) == 6:
                update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "commissions": 0.0})
                st.success("Account Created!")

# --- 5. INVESTOR PORTAL ---
else:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()
    m_on = is_maintenance_on()

    # Payout Logic
    active_inv = []
    payout = 0
    for i in data.get('inv', []):
        if now >= datetime.fromisoformat(i['end']): payout += (i['amt'] + i['prof'])
        else: active_inv.append(i)
    if payout > 0:
        data['wallet'] += payout
        data['inv'] = active_inv
        update_user(name, data)

    # UI Header
    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>AVAILABLE ASSETS</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='news-card'><b>📢 MARKET UPDATE:</b> {get_status_msg()}</div>", unsafe_allow_html=True)

    # Actions Section
    if m_on:
        st.warning("🚧 SYSTEM MAINTENANCE: Financial actions are temporarily paused.")
    else:
        col_a, col_b = st.columns(2)
        if col_a.button("📥 DEPOSIT"): st.session_state.page = "dep"
        if col_b.button("📤 WITHDRAW"): st.session_state.page = "wd"
    
    if st.session_state.page != "main":
        if st.button("⬅️ DASHBOARD"): st.session_state.page = "main"; st.rerun()

    # Dashboard Content
    if st.session_state.page == "main":
        st.markdown("<div class='section-header'>🚀 DEPLOYMENT CENTER</div>", unsafe_allow_html=True)
        if m_on:
            st.error("Deployments paused for maintenance.")
        else:
            inv_a = st.number_input("Capital PHP", min_value=100.0, step=100.0)
            if st.button("CONFIRM & DEPLOY CAPITAL"):
                if data['wallet'] >= inv_a:
                    data['wallet'] -= inv_a
                    data.setdefault('inv', []).append({"amt": inv_a, "prof": inv_a*0.1, "end": (now + timedelta(hours=24)).isoformat()})
                    update_user(name, data); st.rerun()

        st.markdown("<div class='section-header'>⏳ ACTIVE 24H CYCLES</div>", unsafe_allow_html=True)
        if not active_inv: st.write("No active cycles.")
        for t in active_inv:
            rem = datetime.fromisoformat(t['end']) - now
            st.markdown(f"<div style='background:#1c1e24; padding:20px; border-radius:15px; border:1px solid #3a3d46; text-align:center; margin-bottom:10px;'><p style='color:#8c8f99; margin:0;'>Trade: ₱{t['amt']:,}</p><div style='color:#0dcf70; font-size:2rem; font-weight:bold;'>{str(rem).split('.')[0]}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📜 TRANSACTION LOGS</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"**{t['date']}** | {t['type']} | ₱{t['amt']:,} | `{t['status']}`")

    # Ticker
    ticker_text = f"🔥 FLASH: All 24H cycles closed with +10% gains. &nbsp;&nbsp;&nbsp; ✅ Payout to {random.randint(100,999)} completed!"
    st.markdown(f"<div class='ticker-wrap'><marquee>{ticker_text}</marquee></div>", unsafe_allow_html=True)
    st.write("<br><br><br>", unsafe_allow_html=True)

# --- 6. ⚠️ THE HIDDEN BOSS PANEL ---
st.divider()
with st.expander("⚠️"):
    boss_input = st.text_input("Key", type="password", label_visibility="collapsed")
    if st.button("ENTER"):
        if boss_input == "Orange01!":
            st.session_state.is_boss = True; st.success("Boss Mode Active")
        else: st.error("Denied")

if st.session_state.is_boss:
    st.divider()
    all_users = load_registry()
    total_val = sum(u.get('wallet', 0.0) for u in all_users.values())
    st.metric("💰 TOTAL SYSTEM ASSETS", f"₱{total_val:,.2f}")
    
    adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(["🔔 APPROVE", "🛠️ ADJUST", "📢 SYSTEM", "💾 BACKUP"])
    
    with adm_tab1:
        st.subheader("Pending Approvals")
        for un, ud in all_users.items():
            for i, tx in enumerate(ud.get('tx', [])):
                if tx['type'] == 'DEP' and tx['status'] == 'PENDING':
                    st.info(f"{un}: ₱{tx['amt']:,}")
                    if st.button(f"Approve {un}", key=f"a_{un}_{i}"):
                        all_users[un]['wallet'] += tx['amt']; all_users[un]['tx'][i]['status'] = 'APPROVED'
                        with open(REGISTRY_FILE, "w") as f: json.dump(all_users, f, default=str)
                        st.rerun()
    
    with adm_tab2:
        st.subheader("Manual Balance Update")
        if all_users:
            target = st.selectbox("Select Investor", list(all_users.keys()))
            mod_amt = st.selectbox("Amount (PHP)", options=[500, 1000, 5000, 10000, 50000])
            if st.button(f"ADD ₱{mod_amt:,} TO {target}"):
                all_users[target]['wallet'] += mod_amt
                all_users[target].setdefault('tx', []).append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "type": "ADMIN_ADJ", "amt": mod_amt, "status": "COMPLETED"})
                with open(REGISTRY_FILE, "w") as f: json.dump(all_users, f, default=str)
                st.success("Updated & Logged!"); st.rerun()
                
    with adm_tab3:
        st.subheader("Global Settings")
        m_state = st.toggle("MAINTENANCE MODE", value=is_maintenance_on())
        fee_val = st.number_input("Withdrawal Fee %", value=get_wd_fee(), step=0.5)
        if st.button("SAVE SYSTEM CHANGES"):
            set_maintenance(m_state); set_wd_fee(fee_val); st.success("System Updated")
        st.divider()
        new_msg = st.text_area("Market Update Broadcast:", value=get_status_msg())
        if st.button("PUSH BROADCAST"): set_status_msg(new_msg); st.rerun()
                
    with adm_tab4:
        st.subheader("Data Export")
        if all_users:
            df = pd.DataFrame.from_dict(all_users, orient='index')
            st.download_button("📥 DOWNLOAD CSV", df.to_csv().encode('utf-8'), "BPSM_Backup.csv", "text/csv")
    
    if st.button("LOGOUT BOSS"): st.session_state.is_boss = False; st.rerun()

time.sleep(1); st.rerun()
    
