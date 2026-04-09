import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import json

# ==========================================
# BLOCK 1: CLOUD DATA ENGINE (FIREBASE)
# ==========================================
try:
    creds_info = st.secrets["firebase"]
    creds = service_account.Credentials.from_service_account_info(creds_info)
    db = firestore.Client(credentials=creds)
except Exception as e:
    st.error("Database connection failed. Check your Streamlit Secrets.")

def load_registry():
    try:
        users_ref = db.collection("investors")
        docs = users_ref.stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception:
        return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

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
            label = f"{action['type']} - {username} - ₱{action.get('amount', 0):,.2f}"
            with st.expander(label):
                if action['type'] == "WITHDRAW":
                    st.warning(f"**BANK:** {action.get('bank')}\n\n**ACCT #:** {action.get('acct_num')}\n\n**NAME:** {action.get('acct_name')}")
                
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

                    u_data.setdefault('history', []).append({"type": action['type'], "amount": action['amount'], "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"})
                    u_data['pending_actions'].pop(idx)
                    update_user(username, u_data); st.rerun()
                
                if cr.button("❌ REJECT", key=f"rej_{username}_{idx}"):
                    if action['type'] == "WITHDRAW":
                        u_data['wallet'] = u_data.get('wallet', 0.0) + action['amount'] 
                    u_data['pending_actions'].pop(idx); update_user(username, u_data); st.rerun()

# ==========================================
# BLOCK 4: USER DASHBOARD
# ==========================================
elif st.session_state.user:
    reg = load_registry()
    data = reg.get(st.session_state.user, {})
    user_display = str(st.session_state.user).upper()
    current_wallet = float(data.get('wallet', 0.0))

    st.write(f"Logged in as: **{user_display}**")
    if st.button("LOGOUT"):
        st.session_state.user = None; st.session_state.page = "ad"; st.rerun()

    st.markdown(f"""<div class="balance-box"><p style="color:#8c8f99; font-size:12px; margin-bottom:5px;">WITHDRAWABLE BALANCE</p><h1 style="color:#00ff88; font-size:45px; margin:0;">₱{current_wallet:,.2f}</h1></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("📥 DEPOSIT"): st.session_state.action_type = "DEP"
    if c2.button("💸 WITHDRAW"): st.session_state.action_type = "WITH"
    if c3.button("♻️ REINVEST"): st.session_state.action_type = "REIN"

    if st.session_state.action_type == "DEP":
        with st.form("d"):
            st.markdown("### 📥 DEPOSIT REQUEST")
            st.info("💳 **GCASH:** 09XXXXXXXX | **NAME:** T*** S*** T.")
            amt_d = st.number_input("Amount (Min: ₱500)", min_value=500.0)
            uploaded_file = st.file_uploader("Browse Receipt", type=['jpg', 'jpeg', 'png'])
            if st.form_submit_button("SEND TO ADMIN"):
                if uploaded_file:
                    data.setdefault('pending_actions', []).append({"type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    data.setdefault('history', []).append({"type": "DEPOSIT", "amount": amt_d, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "PENDING"})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.error("Please upload your receipt.")

    if st.session_state.action_type == "REIN":
        with st.form("r"):
            st.markdown("### ♻️ REINVEST CAPITAL")
            amt_r = st.number_input("Amount to Reinvest", min_value=0.0, max_value=max(0.0, current_wallet), step=100.0)
            if st.form_submit_button("CONFIRM REINVESTMENT"):
                if amt_r > 0 and amt_r <= current_wallet:
                    data['wallet'] = current_wallet - amt_r
                    data.setdefault('inv', []).append({"amount": amt_r, "start_time": datetime.now().isoformat()})
                    data.setdefault('history', []).append({"type": "REINVEST", "amount": amt_r, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.error("Invalid amount or insufficient balance.")

    if st.session_state.action_type == "WITH":
        with st.form("w"):
            st.markdown("### 💸 WITHDRAWAL REQUEST")
            amt_w = st.number_input("Withdrawal Amount", min_value=0.0, max_value=max(0.0, current_wallet), step=100.0)
            bank_n = st.text_input("Bank / Wallet Name")
            acct_num = st.text_input("Account Number")
            acct_name = st.text_input("Account Name")
            if st.form_submit_button("SUBMIT WITHDRAWAL"):
                if amt_w > 0 and bank_n and acct_num and acct_name:
                    data['wallet'] = current_wallet - amt_w
                    data.setdefault('pending_actions', []).append({"type": "WITHDRAW", "amount": amt_w, "bank": bank_n, "acct_num": acct_num, "acct_name": acct_name, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    data.setdefault('history', []).append({"type": "WITHDRAW", "amount": amt_w, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "PENDING"})
                    update_user(st.session_state.user, data); st.session_state.action_type = None; st.rerun()
                else: st.error("Check balance and fill all details.")

    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active: 
        st.info("No running capitals.")
    else:
        now = datetime.now()
        for idx, a in reversed(list(enumerate(active))):
            start_dt = datetime.fromisoformat(a['start_time'])
            unlock_dt = start_dt + timedelta(days=7)
            total_seconds = 7 * 86400
            elapsed = (now - start_dt).total_seconds()
            progress = min(1.0, elapsed / total_seconds)
            total_roi = a['amount'] * 1.20
            live_profit = (a['amount'] * 0.20) * progress
            unlock_str = unlock_dt.strftime("%b %d, %Y at %I:%M %p")
            
            st.markdown(f"""
                <div class='hist-card'>
                    <span class='roi-text'>ROI: ₱{total_roi:,.2f}</span>
                    <b>CAPITAL: ₱{a['amount']:,.2f}</b><br>
                    <div class='live-profit'>
                        LIVE PROFIT: ₱{live_profit:,.2f}<br>
                        📅 UNLOCKS: {unlock_str}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.progress(progress)
            is_locked = now < unlock_dt
            btn_label = f"📥 PULL OUT ₱{total_roi:,.2f}" if not is_locked else "🔒 LOCKED"
            if st.button(btn_label, key=f"p_{idx}", disabled=is_locked):
                data['wallet'] = current_wallet + total_roi
                data.setdefault('history', []).append({"type": "PULL_OUT", "amount": total_roi, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "CONFIRMED"})
                active.pop(idx)
                update_user(st.session_state.user, data); st.rerun()

    st.divider()
    st.markdown("### 🤝 REFERRAL PROGRAM")
    st.code(f"https://ismex-philippines.streamlit.app/?ref={user_display.replace(' ', '+')}", language="text")

    comms = data.get('commissions', [])
    if comms:
        for idx, c in enumerate(comms):
            st.write(f"👤 {c['referee']} | ₱{c['amt']:,.2f} | **{c['status']}**")
            if c['status'] == "UNCLAIMED" and st.button(f"CLAIM ₱{c['amt']}", key=f"c_{idx}"):
                data.setdefault('pending_actions', []).append({"type": "COMMISSION_REQUEST", "amount": c['amt'], "comm_index": idx})
                update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 TRANSACTION HISTORY")
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
            if u in reg and str(reg[u]['pin']) == str(p): 
                st.session_state.user = u; st.rerun()
            else: st.error("Invalid Login")
    with t2:
        fn = st.text_input("NAME MIDDLE LAST").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        rn = st.text_input("REFERRAL NAME", value=current_ref).upper().strip()
        if st.button("REGISTER"):
            reg = load_registry()
            if fn in reg:
                st.error("ACCESS DENIED: Name already exists.")
            elif fn and len(p1) == 6:
                user_data = {"pin": p1, "wallet": 0.0, "inv": [], "full_name": fn, "referral": rn, "pending_actions": [], "history": [], "commissions": [], "has_deposited": False}
                update_user(fn, user_data); st.success("Registered! Login now.")
else:
    st.markdown("<h1 style='color: #007BFF;'>INTERNATIONAL STOCK MARKET EXCHANGE! 📊📈</h1>", unsafe_allow_html=True)
    st.write("Grow your capital by 20% every 7 days!")
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 PRESS HERE TO REGISTER / LOGIN", use_container_width=True): 
        st.session_state.page = "login"; st.rerun()
    if st.session_state.admin_mode:
        if st.text_input("error execution", type="password") == "0102030405": 
            st.session_state.is_boss = True; st.rerun()
            
