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
if 'action_type' not in st.session_state: st.session_state.action_type = None

# ==========================================
# BLOCK 2: UI STYLES & ABSOLUTE LOCKDOWN
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

if "ref" in st.query_params:
    st.session_state.url_ref = st.query_params["ref"].replace("+", " ").upper().strip()
current_ref = st.session_state.get("url_ref", "")

st.markdown("""
    <style>
    header, footer, #MainMenu, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] {
        visibility: hidden !important; display: none !important;
    }
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button {
        background-color: #1c1e26 !important; color: #ffffff !important;
        border: 2px solid #333 !important; border-radius: 8px !important;
        font-weight: bold !important; width: 100% !important;
    }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 2px; border-left: 5px solid #00ff88; }
    .roi-text { color: #00ff88; font-weight: bold; float: right; font-size: 18px; }
    .live-profit { color: #8c8f99; font-size: 14px; margin-top: 5px; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: ADMIN PANEL
# ==========================================
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL CENTER")
    if st.button("EXIT ADMIN"):
        st.session_state.is_boss = False; st.rerun()
    
    reg = load_registry()
    st.subheader("🔔 PENDING APPROVALS")
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(list(pending_list)):
            with st.expander(f"{action['type']} - {username} - ₱{action.get('amount', 0):,.2f}"):
                ca, cr = st.columns(2)
                if ca.button("✅ APPROVE", key=f"app_{username}_{idx}"):
                    if action['type'] == "DEPOSIT":
                        if not u_data.get('has_deposited'):
                            ref_name = u_data.get('referral')
                            if ref_name in reg:
                                commission = action['amount'] * 0.20
                                reg[ref_name].setdefault('commissions', []).append({
                                    "referee": username, "deposit": action['amount'],
                                    "amt": commission, "status": "UNCLAIMED"
                                })
                            u_data['has_deposited'] = True
                        u_data.setdefault('inv', []).append({"amount": action['amount'], "start_time": datetime.now().isoformat()})
                    
                    elif action['type'] == "COMMISSION_REQUEST":
                        u_data['wallet'] = u_data.get('wallet', 0.0) + action['amount']
                        c_idx = action.get('comm_index')
                        if c_idx is not None and len(u_data.get('commissions', [])) > c_idx:
                            u_data['commissions'][c_idx]['status'] = "CLAIMED"

                    # History update on approval
                    u_data.setdefault('history', []).append({
                        "type": action['type'], 
                        "amount": action['amount'], 
                        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), 
                        "status": "CONFIRMED"
                    })
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()
                
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    u_data['pending_actions'].pop(idx); update_user(username, u_data); st.rerun()

# ==========================================
# BLOCK 4: USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    user_display = str(st.session_state.user).upper()

    st.write(f"Logged in as: **{user_display}**")
    if st.button("LOGOUT"):
        st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    st.markdown(f"""<div class="balance-box"><p style="color:#8c8f99; font-size:12px; margin-bottom:5px;">WITHDRAWABLE BALANCE</p><h1 style="color:#00ff88; font-size:45px; margin:0;">₱{data.get('wallet', 0.0):,.2f}</h1></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.markdown("### 📥 DEPOSIT REQUEST")
            st.info("💳 **GCASH:** 09XXXXXXXX | **NAME:** T*** S*** T.")
            amt_d = st.number_input("Amount (Min: ₱500)", min_value=500.0)
            # RESTORED BROWSE RECEIPT
            uploaded_file = st.file_uploader("Browse Receipt", type=['jpg', 'jpeg', 'png'])
            if st.form_submit_button("SEND TO ADMIN"):
                if uploaded_file:
                    data.setdefault('pending_actions', []).append({
                        "type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    # Add to history as pending
                    data.setdefault('history', []).append({
                        "type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "PENDING"
                    })
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else:
                    st.error("Please upload your receipt.")

    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in reversed(list(enumerate(active))):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            progress = min(1.0, (now - start_dt).total_seconds() / (7 * 86400))
            total_roi = a['amount'] * 1.20
            live_profit = (a['amount'] * 0.20) * progress
            st.markdown(f"""<div class='hist-card'><span class='roi-text'>ROI: ₱{total_roi:,.2f}</span><b>CAPITAL: ₱{a['amount']:,.2f}</b><br><div class='live-profit'>LIVE PROFIT: ₱{live_profit:,.2f}</div></div>""", unsafe_allow_html=True)
            st.progress(progress)
            if st.button(f"📥 PULL OUT ₱{total_roi:,.2f}", key=f"p_{idx}", disabled=not (progress >= 1.0)):
                data['wallet'] = data.get('wallet', 0.0) + total_roi
                data.setdefault('history', []).append({"type": "PULL_OUT", "amount": total_roi, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"})
                active.pop(idx); update_user(st.session_state.user, data); st.rerun()

    st.divider()

    st.markdown("### 🤝 REFERRAL PROGRAM")
    my_link = f"https://twee-gith.github.io/ISMEX-PHILIPPINES/?ref={user_display.replace(' ', '+')}"
    st.code(my_link, language="text")

    comms = data.get('commissions', [])
    if comms:
        for idx, c in enumerate(comms):
            st.write(f"👤 {c['referee']} | ₱{c['amt']:,.2f} | **{c['status']}**")
            if c['status'] == "UNCLAIMED" and st.button(f"CLAIM ₱{c['amt']}", key=f"c_{idx}"):
                data.setdefault('pending_actions', []).append({"type": "COMMISSION_REQUEST", "amount": c['amt'], "comm_index": idx})
                update_user(st.session_state.user, data); st.rerun()
    else:
        st.info("No referral commissions yet.")

    st.markdown("### 📜 TRANSACTION HISTORY")
    # All transactions (including pending ones from history list) appear here
    for h in reversed(data.get('history', [])):
        st.write(f"✅ **{h.get('status', 'CONFIRMED')}**: {h['type']} - ₱{h['amount']:,.2f} | {h['date']}")

# ==========================================
# BLOCK 5: LOGIN & LANDING
# ==========================================
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
        fn = st.text_input("NAME MIDDLE LAST").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        rn = st.text_input("REFERRAL NAME", value=current_ref).upper().strip()
        if st.button("REGISTER"):
            reg = load_registry()
            if fn and len(p1) == 6:
                reg[fn] = {"pin": p1, "wallet": 0.0, "inv": [], "full_name": fn, "referral": rn, "pending_actions": [], "history": [], "commissions": [], "has_deposited": False}
                update_user(fn, reg[fn]); st.success("Registered! Login now.")
else:
    st.markdown("<h1 style='color: #007BFF;'>INTERNATIONAL STOCK MARKET EXCHANGE! 📊📈</h1>", unsafe_allow_html=True)
    st.write("Transform your initial investment into a powerhouse of growth through our precision-engineered market cycles.")
    st.info("### 🚀 Grow your capital by 20% every 7 days!")
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 PRESS HERE TO REGISTER / LOGIN", use_container_width=True): st.session_state.page = "login"; st.rerun()
    if st.session_state.admin_mode:
        if st.text_input("code", type="password") == "0102030405": st.session_state.is_boss = True; st.rerun()
            
