import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

# --- 1. DATA STORAGE ---
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

# --- 2. GLOBAL STYLES (LOCKED TO SCREENSHOTS) ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    
    /* Withdrawable Balance Card */
    .balance-card { 
        background: #1c1e24; padding: 20px; border-radius: 10px; 
        border: 1px solid #3a3d46; text-align: center; margin-bottom: 15px; 
    }
    .balance-label { color: #8c8f99; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .balance-val { color: #00ff88; font-size: 38px; font-weight: bold; margin: 0; }
    
    /* News Ticker */
    .news-box { background: #ce112610; border-left: 4px solid #ce1126; padding: 10px; margin-bottom: 20px; border-radius: 0 8px 8px 0; }
    
    /* Section Headers (cite: 8823.jpg, 8824.jpg) */
    .section-header { 
        background: #252830; padding: 10px; border-radius: 5px; 
        margin-top: 15px; font-weight: bold; border-left: 5px solid #ce1126; 
        color: white; text-transform: uppercase; font-size: 14px;
    }
    
    /* Main Content Cards (cite: 8820.jpg, 8823.jpg) */
    .user-box { 
        background-color: #1c1e24; padding: 20px; border-radius: 12px; 
        border: 1px solid #3a3d46; margin-bottom: 5px; border-left: 6px solid #00ff88; 
    }
    .roi-text { color: #00ff88; font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; line-height: 1.2; }
    .meta-label { color: #8c8f99; font-size: 14px; }
    
    /* Pull Out / Action Buttons (cite: 8823.jpg) */
    .stButton>button { 
        width: 100%; border-radius: 6px; padding: 12px; 
        background-color: #252830; border: 1px solid #3a3d46; 
        color: #8c8f99; font-size: 13px; text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

NEWS_HEADLINES = [
    "📈 PSEi index climbs as blue-chip stocks rally.",
    "🚀 Tech sector sees 5% growth in morning trade.",
    "🏦 Bangko Sentral hints at steady interest rates.",
    "📊 Market analysts predict a bullish trend this week."
]

# --- 3. SESSION & LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if st.session_state.user is None and not st.session_state.is_boss:
    st.title("BAGONG PILIPINAS STOCK MARKET")
    t1, t2 = st.tabs(["SIGN-IN", "REGISTER"])
    with t1:
        ln, lp = st.text_input("NAME").upper(), st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln; st.rerun()
    with t2:
        rn = st.text_input("FULL NAME", key="r1").upper()
        rp = st.text_input("CREATE PIN", type="password", key="r2")
        ref = st.text_input("REFERRER NAME", key="r3").upper()
        if st.button("REGISTER ACCOUNT"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "reg_date": datetime.now().strftime("%Y-%m-%d"), "bonus_status": {}})
            st.success("SUCCESSFUL"); st.rerun()
    with st.expander("🔐 ADMIN"):
        if st.text_input("ADMIN PIN", type="password") == "0102030405":
            if st.button("ENTER BOSS MODE"): st.session_state.is_boss = True; st.rerun()
    st.stop()



# --- FULL CORRECTED INVESTOR DASHBOARD ---
if st.session_state.user:
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()

# --- 6. DEPOSIT SECTION (ADD THIS INSIDE THE USER DASHBOARD BLOCK) ---
st.markdown("<div class='section-header'>📥 DEPOSIT CAPITAL</div>", unsafe_allow_html=True)
with st.container():
    dep_amt = st.number_input("Amount to Deposit", min_value=500, step=500, key="dep_input")
    if st.button("SUBMIT DEPOSIT REQUEST"):
        # We ensure 'tx' exists in the user's dictionary
        if 'tx' not in data:
            data['tx'] = []
            
        new_tx = {
            "amt": dep_amt,
            "type": "DEPOSIT",
            "status": "PENDING_DEP",
            "date": datetime.now().isoformat()
        }
        
        data['tx'].append(new_tx)
        update_user(name, data) # This saves it back to the JSON
        st.success(f"Request for ₱{dep_amt:,} sent! Waiting for Admin approval.")
        st.rerun()
        
    
    # 1. ROI CALC ENGINE
    MINUTE_RATE = (0.20 / 7) / 1440 
    changed = False
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        calc_now = min(now, et_t)
        i['accumulated_roi'] = max(0, i['amt'] * (((calc_now - st_t).total_seconds() / 60) * MINUTE_RATE))
        if now >= et_t and not i.get('roi_paid', False):
            data['wallet'] += (i['amt'] * 0.20); i['roi_paid'] = True; changed = True
        if now >= (et_t + timedelta(hours=1)):
            i.update({"start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat(), "roi_paid": False}); changed = True
    if changed: update_user(name, data); st.rerun()

    # 2. BALANCE DISPLAY
    st.markdown(f"""
        <div class="balance-card">
            <p class="balance-label">WITHDRAWABLE BALANCE</p>
            <p class="balance-val">₱{data['wallet']:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

    # 3. ACTIVE CYCLES
    st.markdown("<div class='section-header'>⌛ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    inv_list = data.get('inv', [])
    for idx, t in enumerate(reversed(inv_list)):
        actual_idx = len(inv_list) - 1 - idx
        st_t, et_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
        grace_end = et_t + timedelta(hours=1)
        
        st.markdown(f"""
            <div class='user-box'>
                <b>Capital: ₱{t['amt']:,}</b><br>
                <span class='roi-text'>Accumulated ROI: ₱{t.get('accumulated_roi', 0):,.4f}</span><br>
                <span class='meta-label'>Total to Receive: ₱{t['amt']*0.20:,.2f}</span><br><br>
                <b>Approved:</b> {st_t.strftime('%Y-%m-%d %I:%M %p')}<br>
                <b>Maturity:</b> {et_t.strftime('%Y-%m-%d %I:%M %p')}<br>
                <b style='color:#ff4b4b;'>⌛ TIME REMAINING: {str(et_t - now).split('.')[0] if now < et_t else 'MATURED'}</b>
            </div>
        """, unsafe_allow_html=True)

        btn_lbl = f"AVAILABLE TO PULL OUT CAPITAL FROM {et_t.strftime('%I:%M %p')} TO {grace_end.strftime('%I:%M %p')}"
        if et_t <= now < grace_end:
            if st.button(f"✅ PULL CAPITAL (₱{t['amt']:,})", key=f"act_p_{actual_idx}"):
                data['wallet'] += t['amt']; data['inv'].pop(actual_idx); update_user(name, data); st.rerun()
        else:
            st.button(btn_lbl, key=f"act_l_{actual_idx}", disabled=True)

    # 4. REFERRAL COMMISSIONS (EXACT MATCH FOR 8824.jpg)
    all_u = load_registry()
    referrals = {u_n: u_i for u_n, u_i in all_u.items() if u_i.get('ref_by') == name}

    for u_n, u_i in referrals.items():
        # Get the first successful deposit to calculate bonus
        f_dep = next((tx['amt'] for tx in u_i.get('tx', []) if tx['status'] == "SUCCESSFUL_DEP"), 0)
        
        if f_dep > 0:
            comm_val = f_dep * 0.20
            b_status = data.get('bonus_status', {}).get(u_n, "AVAILABLE")
            
            # Header repeats for each referral card as seen in 8824.jpg
            st.markdown("<div class='section-header'>👥 REFERRAL COMMISSIONS</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class='user-box'>
                    <b>Capital: ₱{f_dep:,.1f}</b><br>
                    <span class='roi-text'>Accumulated ROI: ₱{comm_val:,.4f}</span><br>
                    <span class='meta-label'>Total to Receive: ₱{comm_val:,.2f}</span><br><br>
                    <b>Invitee:</b> {u_n}<br>
                    <b>Registered:</b> {u_i.get('reg_date', 'N/A')}<br>
                    <b style='color:#ff4b4b;'>⌛ STATUS: {b_status}</b>
                </div>
            """, unsafe_allow_html=True)

            if b_status == "AVAILABLE":
                if st.button(f"CLAIM BONUS FROM {u_n}", key=f"ref_btn_{u_n}"):
                    data.setdefault('bonus_status', {})[u_n] = "REQUESTED"; update_user(name, data); st.rerun()
            else:
                st.button(f"BONUS {b_status}", key=f"ref_stat_{u_n}", disabled=True)

    # 5. LOGOUT (OUTSIDE LOOPS)
    st.write("---")
    if st.button("LOGOUT", key="dash_logout"): 
        st.session_state.user = None
        st.rerun()
        
            
        

# --- 5. ADMIN OVERVIEW ---
elif st.session_state.is_boss:
    st.title("👑 BOSS OVERVIEW")
    all_users = load_registry()
    for u_name, u_data in all_users.items():
        with st.expander(f"USER: {u_name} | Wallet: ₱{u_data.get('wallet'):,.2f}"):
            for idx, tx in enumerate(u_data.get('tx', [])):
                if tx['status'] == "PENDING_DEP":
                    if st.button(f"APPROVE ₱{tx['amt']:,}", key=f"a_{u_name}_{idx}"):
                        st_t = datetime.now()
                        tx['status'] = "SUCCESSFUL_DEP"
                        u_data.setdefault('inv', []).append({"amt": tx['amt'], "start": st_t.isoformat(), "end": (st_t + timedelta(days=7)).isoformat(), "roi_paid": False})
                        update_user(u_name, u_data); st.rerun()
            for inv_n, status in u_data.get('bonus_status', {}).items():
                if status == "REQUESTED":
                    if st.button(f"PAY BONUS TO {u_name} for {inv_n}"):
                        f_amt = next((t['amt'] for t in all_users[inv_n].get('tx', []) if t['status'] == "SUCCESSFUL_DEP"), 0)
                        u_data['wallet'] += (f_amt * 0.20); u_data['bonus_status'][inv_n] = "RECEIVED"; update_user(u_name, u_data); st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
