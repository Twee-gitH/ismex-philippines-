import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# BLOCK 1: DATA STORAGE ENGINE
# ==========================================
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
        json.dump(reg, f, indent=4, default=str)

# ==========================================
# BLOCK 2: PAGE CONFIG & EXACT CSS (MATCHING 8848.JPG)
# ==========================================
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    /* Global Background & Text */
    .stApp { background-color: #0e1117; }
    
    /* Main Balance Card */
    .balance-card { 
        background: #1c1e24; padding: 30px; border-radius: 15px; 
        border: 1px solid #3a3d46; text-align: center; margin-bottom: 20px; 
    }
    .balance-label { color: #8c8f99; font-size: 14px; text-transform: uppercase; margin-bottom: 5px; }
    .balance-val { color: #00ff88; font-size: 52px; font-weight: bold; margin: 0; }
    
    /* Section Headers */
    .section-header { 
        background: #252830; padding: 12px; border-radius: 5px; 
        margin: 20px 0; font-weight: bold; border-left: 5px solid #ce1126; 
        color: white; text-transform: uppercase; font-size: 15px; 
    }
    
    /* Active Cycle Cards */
    .cycle-card {
        background-color: #1a1c22; padding: 25px; border-radius: 12px;
        border: 1px solid #3a3d46; border-left: 5px solid #00ff88;
        margin-bottom: 15px;
    }
    .peso-symbol { color: #00ff88; font-weight: bold; }
    .capital-text { color: #e0e0e0; font-size: 18px; margin-bottom: 10px; }
    .roi-label-small { color: #00ff88; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .roi-value-large { color: #00ff88; font-size: 48px; font-weight: bold; line-height: 1; margin-bottom: 10px; font-family: monospace; }
    .total-receive { color: #8c8f99; font-size: 14px; margin-bottom: 20px; }
    
    /* Timer & Banner */
    .timer-text { color: #ff4b4b; font-weight: bold; font-size: 17px; margin-bottom: 15px; }
    .pullout-banner {
        background-color: #252830; color: #8c8f99; padding: 15px;
        border-radius: 8px; font-size: 13px; text-align: center;
        border: 1px solid #3a3d46; text-transform: uppercase;
    }

    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 8px; padding: 12px; 
        background-color: #252830; border: 1px solid #3a3d46; 
        color: white; font-weight: bold; text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: SESSION & AUTH
# ==========================================
if 'user' not in st.session_state: st.session_state.user = None
if 'is_boss' not in st.session_state: st.session_state.is_boss = False

if st.session_state.user is None and not st.session_state.is_boss:
    st.title("BAGONG PILIPINAS STOCK MARKET")
    t1, t2 = st.tabs(["SIGN-IN", "REGISTER"])
    with t1:
        ln = st.text_input("NAME")
        lp = st.text_input("PIN", type="password")
        if st.button("LOGIN"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln
                st.rerun()
            elif ln == "ADMIN" and lp == "BOSS": # Backdoor for demo
                st.session_state.is_boss = True
                st.rerun()
            else: st.error("Invalid credentials")
    with t2:
        rn = st.text_input("FULL NAME", key="r1")
        rp = st.text_input("PIN", type="password", key="r2")
        ref = st.text_input("REFERRER", key="r3")
        if st.button("REGISTER ACCOUNT"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "reg_date": datetime.now().strftime("%Y-%m-%d")})
            st.success("SUCCESSFUL - PLEASE LOGIN")

# ==========================================
# BLOCK 4: INVESTOR DASHBOARD (THE ENGINE)
# ==========================================
if st.session_state.user:
    # LIVE REFRESH EVERY 1 SECOND
    st_autorefresh(interval=1000, limit=10000, key="roi_ticker")
    
    name = st.session_state.user
    registry = load_registry()
    data = registry.get(name)
    now = datetime.now()

    # ROI MATH: 20% over 7 days (604,800 seconds)
    ROI_PER_SECOND = 0.20 / 604800

    # Header UI
    c_head1, c_head2 = st.columns([0.8, 0.2])
    with c_head1: st.write(f"Welcome, {name}")
    with c_head2: 
        if st.button("LOGOUT"): 
            st.session_state.user = None
            st.rerun()

    st.markdown(f"""
        <div class="balance-card">
            <p class="balance-label">WITHDRAWABLE BALANCE</p>
            <p class="balance-val"><span class="peso-symbol">₱</span>{data['wallet']:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

            # Action Buttons
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.expander("📥 DEPOSIT"):
            # Check if there's already a pending deposit to show "Waiting"
            pending_deps = [t for t in data.get('tx', []) if t['type'] == "DEP" and t['status'] == "PENDING"]
            
            if pending_deps:
                st.warning("⏳ WAITING FOR ADMIN APPROVAL")
                for p in pending_deps:
                    st.caption(f"Amount: ₱{p['amt']:,} | Sent: {p.get('date', 'Recent')}")
            
            st.divider()
            d_amt = st.number_input("New Deposit Amount", 1000, step=500)
            file = st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'])
            if file and st.button("CONFIRM DEPOSIT"):
                data.setdefault('tx', []).append({
                    "type": "DEP", 
                    "amt": d_amt, 
                    "status": "PENDING", 
                    "date": now.strftime("%Y-%m-%d %I:%M %p")
                })
                update_user(name, data)
                st.rerun()

    with c2:
        with st.expander("💸 WITHDRAW"):
            current_bal = float(data.get('wallet', 0.0))
            w_amt = st.number_input("Amount", min_value=0.0, max_value=max(0.0, current_bal), value=0.0)
            if st.button("CONFIRM WITHDRAW") and w_amt > 0:
                data['wallet'] -= w_amt
                data.setdefault('tx', []).append({"type": "WITH", "amt": w_amt, "status": "PENDING", "date": now.strftime("%Y-%m-%d %I:%M %p")})
                update_user(name, data)
                st.rerun()

    with c3:
        with st.expander("♻️ REINVEST"):
            current_bal = float(data.get('wallet', 0.0))
            r_amt = st.number_input("Reinvest Amount", min_value=0.0, max_value=max(0.0, current_bal), value=0.0)
            if st.button("CONFIRM REINVEST") and r_amt >= 1000:
                data['wallet'] -= r_amt
                data.setdefault('inv', []).append({"amt": r_amt, "start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat(), "roi_paid": False})
                update_user(name, data)
                st.rerun()
                
                
                

    # ==========================================
    # BLOCK 5: LIVE ACTIVE CYCLES
    # ==========================================
    st.markdown("<div class='section-header'>⌛ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    
    inv_list = data.get('inv', [])
    for idx, t in enumerate(reversed(inv_list)):
        actual_idx = len(inv_list) - 1 - idx
        st_t = datetime.fromisoformat(t['start'])
        et_t = datetime.fromisoformat(t['end'])
        
        # Calculate Live Ticking ROI
        if now < et_t:
            elapsed = (now - st_t).total_seconds()
            current_roi = t['amt'] * ROI_PER_SECOND * elapsed
            
            # Time Remaining Formatting
            diff = et_t - now
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{days}D {hours:02}H {minutes:02}M {seconds:02}S"
            banner = f"AVAILABLE TO PULL OUT FROM {et_t.strftime('%b %d, %I:%M %p')}"
            matured = False
        else:
            current_roi = t['amt'] * 0.20
            time_str = "MATURED"
            banner = "READY TO PULL OUT CAPITAL"
            matured = True
            # Auto-pay ROI to wallet once
            if not t.get('roi_paid', False):
                data['wallet'] += current_roi
                t['roi_paid'] = True
                update_user(name, data)

        # HTML Component for Card
        st.markdown(f"""
            <div class="cycle-card">
                <div class="capital-text">Capital: <span class="peso-symbol">₱</span>{t['amt']:,.1f}</div>
                <div class="roi-label-small">ACCUMULATED ROI:</div>
                <div class="roi-value-large"><span class="peso-symbol">₱</span>{current_roi:,.4f}</div>
                <div class="total-receive">Total to Receive: ₱{t['amt']*0.20:,.2f}</div>
                <div class="timer-text">⌛ TIME REMAINING: {time_str}</div>
                <div class="pullout-banner">{banner}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if matured:
            if st.button(f"✅ PULL OUT CAPITAL (₱{t['amt']:,})", key=f"pull_{actual_idx}"):
                data['wallet'] += t['amt']
                data['inv'].pop(actual_idx)
                update_user(name, data)
                st.rerun()

# ==========================================
# BLOCK 6: BOSS ADMIN PANEL
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 ADMIN OVERVIEW")
    all_u = load_registry()
    for u_n, u_d in all_u.items():
        for tx in u_d.get('tx', []):
            if tx['status'] == "PENDING":
                st.info(f"USER: {u_n} | {tx['type']} | ₱{tx['amt']}")
                if st.button(f"APPROVE {u_n} ##{random.randint(1,999)}"):
                    tx['status'] = "SUCCESSFUL"
                    if tx['type'] == "DEP":
                        u_d.setdefault('inv', []).append({"amt": tx['amt'], "start": datetime.now().isoformat(), "end": (datetime.now() + timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(u_n, u_d); st.rerun()
    if st.button("EXIT ADMIN"): 
        st.session_state.is_boss = False
        st.rerun()
    
