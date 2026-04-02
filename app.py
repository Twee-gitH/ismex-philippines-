import streamlit as st
import json
import os
from datetime import datetime, timedelta

# ==========================================
# BLOCK 1: CORE DATA ENGINE
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

# State initialization
if 'page' not in st.session_state: st.session_state.page = "ad"
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sub_page' not in st.session_state: st.session_state.sub_page = "select"
if 'action_type' not in st.session_state: st.session_state.action_type = None

# ==========================================
# BLOCK 2: UI STYLES
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #00ff88; }
    .stButton>button:contains("⛔") {
        background-color: transparent !important; border: none !important; color: #444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: PAGE ROUTING
# ==========================================

# --- ADMIN PANEL ---
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False
        st.rerun()
    
    reg = load_registry()
    st.subheader("🔔 PENDING APPROVALS")
    found_pending = False
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(list(pending_list)):
            found_pending = True
            with st.expander(f"{action['type']} - {username} (₱{action.get('amount', 0):,.2f})"):
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        # 20% Commission for Referrer on First Deposit
                        if not u_data.get('has_deposited'):
                            ref_name = u_data.get('referral')
                            if ref_name in reg:
                                commission = action['amount'] * 0.20
                                reg[ref_name].setdefault('commissions', []).append({
                                    "referee": username, "deposit": action['amount'],
                                    "amt": commission, "status": "UNCLAIMED"
                                })
                            u_data['has_deposited'] = True
                        # Auto-Run as Capital
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    
                    u_data.setdefault('history', []).append({
                        "type": action['type'], "amount": action['amount'],
                        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"
                    })
                    u_data['pending_actions'].pop(idx)
                    with open("bpsm_registry.json", "w") as f: json.dump(reg, f, indent=4, default=str)
                    st.rerun()
                
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW": u_data['wallet'] += action['amount']
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()

# --- USER DASHBOARD ---
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    if 'wallet' not in data: data['wallet'] = 0.0
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1: st.write(f"Logged in as: **{data.get('full_name')}**")
    with col2:
        if st.button("LOGOUT"):
            st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    st.markdown(f"""
        <div style="background:#1c1e26; padding:20px; border-radius:10px; text-align:center; border:1px solid #00ff88;">
            <p style="color:#8c8f99; font-size:14px;">WITHDRAWABLE BALANCE</p>
            <h1 style="color:#00ff88; font-size:50px; margin:0;">₱{data['wallet']:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    # --- FORMS ---
    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.markdown("### 📥 DEPOSIT REQUEST")
            st.info("💳 **GCASH ACCOUNT:** 09XXXXXXXX | **NAME:** T*** S*** T.")
            amt_d = st.number_input("Amount to Deposit", min_value=100.0)
            uploaded_file = st.file_uploader("Browse Receipt", type=['jpg', 'jpeg', 'png'])
            if st.form_submit_button("SEND TO ADMIN"):
                if uploaded_file:
                    data.setdefault('pending_actions', []).append({
                        "type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "WAITING CONFIRMATION"
                    })
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.error("Please upload receipt.")

    elif st.session_state.action_type == "WITH":
        with st.form("w"):
            st.markdown("### 💸 WITHDRAWAL REQUEST")
            st.warning("⚠️ MINIMUM WITHDRAWAL IS ₱1,000.00")
            amt_w = st.number_input("Amount", min_value=0.0, max_value=max(0.0, float(data['wallet'])))
            b_name = st.text_input("BANK NAME").upper().strip()
            a_name = st.text_input("ACCOUNT NAME").upper().strip()
            a_num = st.text_input("ACCOUNT NUMBER").strip()
            if st.form_submit_button("SUBMIT TO ADMIN"):
                if amt_w < 1000: st.error("Minimum ₱1,000 required.")
                elif not b_name or not a_name or not a_num: st.error("Fill all bank details.")
                else:
                    data['wallet'] -= amt_w
                    data.setdefault('pending_actions', []).append({
                        "type": "WITHDRAW", "amount": amt_w, "bank": b_name, "acc_name": a_name, "acc_num": a_num,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "WITHDRAWAL REQUESTED"
                    })
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    elif st.session_state.action_type == "REIN":
        with st.form("r"):
            st.markdown("### ♻️ REINVEST CAPITAL")
            amt_r = st.number_input("Amount to Reinvest", min_value=100.0, max_value=max(100.0, float(data['wallet'])))
            if st.form_submit_button("CONFIRM REINVESTMENT"):
                if amt_r > data['wallet']: st.error("Insufficient Balance")
                else:
                    data['wallet'] -= amt_r
                    data.setdefault('inv', []).append({"amount": amt_r, "start_time": datetime.now().isoformat()})
                    data.setdefault('history', []).append({
                        "type": "RECYCLE", "amount": amt_r, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "RECYCLE RUNNING"
                    })
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()

    # --- RUNNING CAPITALS ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in enumerate(active):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            total_roi = a['amount'] * 1.20
            days_elapsed = min(7.0, (now - start_dt).total_seconds() / 86400)
            live_profit = (a['amount'] * 0.20) * (max(0, days_elapsed) / 7)
            st.markdown(f"""
                <div class='hist-card'>
                    <div style="display:flex; justify-content:space-between;"><b>CAPITAL: ₱{a['amount']:,.2f}</b><b style="color:#00ff88;">ROI: ₱{total_roi:,.2f}</b></div>
                    <small>LIVE PROFIT: ₱{live_profit:,.2f}</small><br>
                    <small>START: {start_dt.strftime('%Y-%m-%d %I:%M %p')} | END: {end_dt.strftime('%Y-%m-%d %I:%M %p')}</small>
                </div>
            """, unsafe_allow_html=True)
            if now >= end_dt:
                if st.button(f"📥 PULL OUT ₱{total_roi:,.2f}", key=f"p_{idx}"):
                    data['wallet'] += total_roi
                    data.setdefault('history', []).append({"type": "PULL_OUT", "amount": total_roi, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"})
                    active.pop(idx); update_user(st.session_state.user, data); st.rerun()

    # --- REFERRALS ---
    st.markdown("### 🤝 REFERRAL COMMISSIONS (20%)")
    for c_idx, c in enumerate(data.get('commissions', [])):
        col_ref, col_btn = st.columns([0.7, 0.3])
        col_ref.write(f"👤 **{c['referee']}** | Deposit: ₱{c['deposit']:,.2f} | Bonus: **₱{c['amt']:,.2f}**")
        if c['status'] == "UNCLAIMED":
            if col_btn.button(f"CLAIM ₱{c['amt']:,.2f}", key=f"ref_{c_idx}"):
                data['wallet'] += c['amt']; c['status'] = "CLAIMED"
                update_user(st.session_state.user, data); st.rerun()
        else: col_btn.success("✅ CLAIMED")

    # --- HISTORY ---
    st.markdown("### 📜 TRANSACTION HISTORY")
    for p in data.get('pending_actions', []):
        lbl = "WAITING CONFIRMATION" if p['type'] == "DEPOSIT" else "WITHDRAWAL REQUESTED"
        st.write(f"⏳ **{lbl}**: ₱{p['amount']:,.2f} | {p['date']}")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ **{h['status']}**: ₱{h['amount']:,.2f} | {h['date']}")

# --- LOGIN / REGISTER ---
elif st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    if st.button("Back"): st.session_state.page = "ad"; st.rerun()
    t1, t2 = st.tabs(["LOGIN", "REGISTER"])
    with t1:
        u = st.text_input("FULL NAME").upper().strip()
        p = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if u in reg and str(reg[u]['pin']) == str(p): st.session_state.user = u; st.rerun()
            else: st.error("Invalid Login")
    with t2:
        full_name = st.text_input("NAME MIDDLE LAST").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        p2 = st.text_input("CONFIRM PIN", type="password", max_chars=6)
        ref_name = st.text_input("REFERRAL NAME").upper().strip()
        if st.button("REGISTER"):
            reg = load_registry()
            if not full_name or len(p1) != 6 or p1 != p2 or ref_name not in reg: st.error("Check all fields/Referrer")
            else:
                reg[full_name] = {"pin": p1, "wallet": 0.0, "inv": [], "full_name": full_name, "referral": ref_name, "pending_actions": [], "history": [], "commissions": []}
                update_user(full_name, reg[full_name]); st.success("Success! Please Login.")

else:
    st.markdown("<h1 style='color:#007BFF;'>ISMEX OFFICIAL</h1>", unsafe_allow_html=True)
    if st.button("🚀 GET STARTED / LOGIN", use_container_width=True): st.session_state.page = "login"; st.rerun()
    if st.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode and st.text_input("Admin Key", type="password") == "0102030405":
        st.session_state.is_boss = True; st.rerun()
        
