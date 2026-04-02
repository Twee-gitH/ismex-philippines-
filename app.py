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
    for username, u_data in reg.items():
        pending_list = u_data.get('pending_actions', [])
        for idx, action in enumerate(list(pending_list)):
            # Added User Name and PIN to the expander label
            with st.expander(f"{action['type']} - {username} (PIN: {u_data.get('pin')}) - ₱{action.get('amount', 0):,.2f}"):
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
                    update_user(username, u_data)
                    st.rerun()
                    
    st.divider()
    st.subheader("📊 INVESTOR & COMMISSION DATABASE")
    
    # Prepare data for the table
    table_data = []
    for username, u_data in reg.items():
        # Get basic info
        full_name = u_data.get('full_name', username)
        pin = u_data.get('pin', 'N/A')
        
        # Get commission details
        commissions = u_data.get('commissions', [])
        if not commissions:
            # Add user even if they have no invites yet
            table_data.append({
                "Investor Name": full_name,
                "PIN": pin,
                "Invited User": "None",
                "1st Deposit": "₱0.00",
                "Commission": "₱0.00",
                "Status": "-"
            })
        else:
            for c in commissions:
                table_data.append({
                    "Investor Name": full_name,
                    "PIN": pin,
                    "Invited User": c.get('referee', 'N/A'),
                    "1st Deposit": f"₱{c.get('deposit', 0):,.2f}",
                    "Commission": f"₱{c.get('amt', 0):,.2f}",
                    "Status": c.get('status', 'UNCLAIMED')
                })

    # Display the Table
    if table_data:
        st.table(table_data)
    else:
        st.info("No investors found in registry.")
                                  
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
                else: st.error("Upload receipt.")

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
                elif not b_name or not a_name or not a_num: st.error("Fill all details.")
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

        # --- 1st DISPLAY: RUNNING CAPITALS (NEWEST ON TOP) ---
    st.markdown("### 🚀 RUNNING CAPITALS")
    active = data.get('inv', [])
    if not active:
        st.info("No running capitals.")
    else:
        now = datetime.now()
        # reversed() ensures the latest added capital is displayed first
        for idx, a in reversed(list(enumerate(active))):
            start_dt = datetime.fromisoformat(a['start_time'])
            end_dt = start_dt + timedelta(days=7)
            total_roi = a['amount'] * 1.20
            days_elapsed = min(7.0, (now - start_dt).total_seconds() / 86400)
            live_profit = (a['amount'] * 0.20) * (max(0, days_elapsed) / 7)
            
            st.markdown(f"""
                <div class='hist-card'>
                    <div style="display:flex; justify-content:space-between;">
                        <b>CAPITAL: ₱{a['amount']:,.2f}</b>
                        <b style="color:#00ff88;">ROI: ₱{total_roi:,.2f}</b>
                    </div>
                    <small>LIVE PROFIT: ₱{live_profit:,.2f}</small><br>
                    <small>START: {start_dt.strftime('%Y-%m-%d %I:%M %p')} | END: {end_dt.strftime('%Y-%m-%d %I:%M %p')}</small>
                </div>
            """, unsafe_allow_html=True)
            
            if now >= end_dt:
                if st.button(f"📥 PULL OUT ₱{total_roi:,.2f}", key=f"p_{idx}"):
                    data['wallet'] += total_roi
                    data.setdefault('history', []).append({
                        "type": "PULL_OUT", 
                        "amount": total_roi, 
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                        "status": "CONFIRMED"
                    })
                    active.pop(idx)
                    update_user(st.session_state.user, data)
                    st.rerun()
                    

        st.markdown("### 🤝 REFERRAL COMMISSIONS (20%)")
    comms = data.get('commissions', [])
    
    if not comms:
        st.info("No referral commissions yet.")
    else:
        # Create a clean table for the user to see their invites
        user_table = []
        for idx, c in enumerate(comms):
            status = c.get('status', 'UNCLAIMED')
            
            # Action logic for the status column
            if status == "UNCLAIMED":
                display_status = "Ready to Request"
            elif status == "REQUESTED":
                display_status = "⏳ Pending Admin"
            else:
                display_status = "✅ Received"

            user_table.append({
                "Invite Name": c.get('referee'),
                "1st Deposit": f"₱{c.get('deposit', 0):,.2f}",
                "Bonus": f"₱{c.get('amt', 0):,.2f}",
                "Status": display_status
            })
        
        # Show the table to the user
        st.table(user_table)

        # Show Request Buttons only for UNCLAIMED ones
        for idx, c in enumerate(comms):
            if c.get('status') == "UNCLAIMED":
                if st.button(f"Request Bonus from {c['referee']}", key=f"req_{idx}"):
                    c['status'] = "REQUESTED"
                    data.setdefault('pending_actions', []).append({
                        "type": "COMMISSION_REQUEST",
                        "amount": c['amt'],
                        "referee": c['referee'],
                        "comm_index": idx,
                        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")
                    })
                    update_user(st.session_state.user, data)
                    st.rerun()
                    
            
    st.markdown("### 📜 TRANSACTION HISTORY")
    for p in data.get('pending_actions', []):
        lbl = "WAITING CONFIRMATION" if p['type'] == "DEPOSIT" else "WITHDRAWAL REQUESTED"
        st.write(f"⏳ **{lbl}**: ₱{p['amount']:,.2f} | {p['date']}")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ **{h['status']}**: ₱{h['amount']:,.2f} | {h['date']}")

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
        with t2:.
        fn = st.text_input("NAME MIDDLE LAST").upper().strip()
        p1 = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
        p2 = st.text_input("CONFIRM PIN", type="password", max_chars=6)
        rn = st.text_input("REFERRAL NAME (Must be an Active Investor)").upper().strip()
        
        if st.button("REGISTER"):
            reg = load_registry()
            
            # 1. Check if fields are filled and PINs match
            if not fn or len(p1) != 6 or p1 != p2:
                st.error("Please fill all fields and ensure PINs match (6 digits).")
            
            # 2. Check if Referral exists
            elif rn not in reg:
                st.error(f"Referral Name '{rn}' not found. Please check spelling.")
            
            # 3. Check if Referral is an ACTIVE investor
            else:
                referrer_data = reg[rn]
                if not referrer_data.get('inv') or len(referrer_data.get('inv')) == 0:
                    st.error(f"'{rn}' is not an active investor. Only active investors can refer.")
                else:
                    # Register the user
                    reg[fn] = {
                        "pin": p1, 
                        "wallet": 0.0, 
                        "inv": [], 
                        "full_name": fn, 
                        "referral": rn, 
                        "pending_actions": [], 
                        "history": [], 
                        "commissions": [],
                        "has_deposited": False
                    }
                    update_user(fn, reg[fn])
                    st.success("Registration Successful! You can now Login.")
                    
                    
# RESTORED ORIGINAL FRONT PAGE
else:
    st.markdown("<h1 style='color: #007BFF; margin-bottom: 0;'>ISMEX OFFICIAL</h1>", unsafe_allow_html=True)
    st.markdown("### Transform your initial investment into a powerhouse of growth through our precision-engineered market cycles.")
    st.divider()
    st.info("### 🚀 Grow your capital by 20% every 7 days.")
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"): st.session_state.admin_mode = not st.session_state.admin_mode
    if col_b.button("🚀 GET STARTED / LOGIN", use_container_width=True): st.session_state.page = "login"; st.rerun()
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True; st.rerun()
                    
