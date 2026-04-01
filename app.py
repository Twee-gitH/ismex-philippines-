# ==========================================
# BLOCK 1: IMPORTS & DATA STORAGE
# ==========================================
import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

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

# ==========================================
# BLOCK 2: GLOBAL STYLES (MATCHING PHOTOS)
# ==========================================
st.set_page_config(page_title="BPSM Official", layout="wide")
st.markdown("""
    <style>
    input[type="text"] { text-transform: uppercase !important; }
    .balance-card { background: #1c1e24; padding: 20px; border-radius: 10px; border: 1px solid #3a3d46; text-align: center; margin-bottom: 15px; }
    .balance-label { color: #8c8f99; font-size: 12px; text-transform: uppercase; }
    .balance-val { color: #00ff88; font-size: 38px; font-weight: bold; margin: 0; }
    .section-header { background: #252830; padding: 10px; border-radius: 5px; margin-top: 15px; font-weight: bold; border-left: 5px solid #ce1126; color: white; text-transform: uppercase; font-size: 14px; }
    
    .user-box { background-color: #1c1e24; padding: 20px; border-radius: 12px; border: 1px solid #3a3d46; margin-bottom: 5px; border-left: 6px solid #00ff88; }
    .roi-label { color: #00ff88; font-size: 28px; font-weight: bold; margin-top: 10px; }
    .roi-text { color: #00ff88; font-family: 'Courier New', monospace; font-size: 38px; font-weight: bold; line-height: 1.2; }
    
    .pull-out-info { 
        border: 1px solid #3a3d46; padding: 15px; border-radius: 8px; 
        text-align: center; background: #1c1e24; color: #8c8f99; 
        font-size: 14px; margin-top: 5px; text-transform: uppercase;
    }
    .stButton>button { width: 100%; border-radius: 6px; padding: 12px; background-color: #252830; border: 1px solid #3a3d46; color: #8c8f99; font-size: 13px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BLOCK 3: SESSION & LOGIN SYSTEM
# ==========================================
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
        rn, rp, ref = st.text_input("FULL NAME", key="r1").upper(), st.text_input("PIN", type="password", key="r2"), st.text_input("REFERRER", key="r3").upper()
        if st.button("REGISTER ACCOUNT"):
            update_user(rn, {"pin": rp, "wallet": 0.0, "inv": [], "tx": [], "ref_by": ref, "reg_date": datetime.now().strftime("%Y-%m-%d")})
            st.success("SUCCESSFUL"); st.rerun()
    with st.expander("🔐 ADMIN"):
        if st.text_input("ADMIN PIN", type="password") == "0102030405":
            if st.button("ENTER BOSS MODE"): st.session_state.is_boss = True; st.rerun()
    st.stop()

# ==========================================
# BLOCK 4: INVESTOR DASHBOARD ENGINE
# ==========================================
if st.session_state.user:
    name = st.session_state.user
    data = load_registry().get(name)
    now = datetime.now()

    # ROI ENGINE (0.20% per cycle)
    MINUTE_RATE = (0.20 / 7) / 1440 
    changed = False
    for i in data.get('inv', []):
        st_t, et_t = datetime.fromisoformat(i['start']), datetime.fromisoformat(i['end'])
        calc_now = min(now, et_t)
        i['accumulated_roi'] = max(0, i['amt'] * (((calc_now - st_t).total_seconds() / 60) * MINUTE_RATE))
        if now >= et_t and not i.get('roi_paid', False):
            data['wallet'] += (i['amt'] * 0.20); i['roi_paid'] = True; changed = True
    if changed: update_user(name, data); st.rerun()

    st.markdown(f'<div class="balance-card"><p class="balance-label">WITHDRAWABLE BALANCE</p><p class="balance-val">₱{data["wallet"]:,.2f}</p></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    # ==========================================
    # BLOCK 5: DEPOSIT (FIXED HIGHLIGHT LOGIC)
    # ==========================================
with c1:
        # --- DEPOSIT CAPITAL BLOCK ---
        with st.expander("📥 DEPOSIT", expanded=True):
            # STEP 1: Enter Amount
            d_amt = st.number_input("Amount (Min 1000)", 1000, step=500, key="dep_amt_input")
            
            # STEP 2: File uploader only appears if amount is confirmed/entered
            if d_amt >= 1000:
                file = st.file_uploader("Upload Receipt", type=['jpg','png','jpeg'], key="dep_file_reg")
                
                # STEP 3: Confirm button only appears after file is uploaded
                if file is not None:
                    # Highlight button green
                    st.markdown('<style>div.stButton > button:first-child { background-color: #00ff88 !important; color: black !important; font-weight: bold; }</style>', unsafe_allow_html=True)
                    
                    if st.button("CONFIRM DEPOSIT", key="confirm_dep_btn"):
                        # FIX: Ensure 'tx' exists so it can be sent to admin
                        if 'tx' not in data: 
                            data['tx'] = []
                        
                        # Add to transaction list for Admin Boss Overview
                        data['tx'].append({
                            "type": "DEP",
                            "amt": d_amt,
                            "status": "PENDING",
                            "receipt": file.name,
                            "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")
                        })
                        
                        update_user(name, data)
                        st.success(f"Deposit of ₱{d_amt:,} sent to Admin!")
                        st.rerun()
                else:
                    st.info("Please upload your receipt to continue.")
            else:
                st.warning("Minimum deposit is ₱1,000")
                

    # ==========================================
    # BLOCK 6: WITHDRAW & REINVEST
    # ==========================================
    with c2:
        with st.expander("💸 WITHDRAW"):
            w_amt = st.number_input("Amount", 100.0, float(data['wallet']) if data['wallet'] > 100 else 100.0, key="w_val")
            bn, an, anum = st.text_input("Bank"), st.text_input("Name"), st.text_input("Number")
            if st.button("CONFIRM WITHDRAW"):
                if data['wallet'] >= w_amt:
                    data['wallet'] -= w_amt
                    data.setdefault('tx', []).append({"type": "WITHDRAW", "amt": w_amt, "status": "PENDING", "bank": bn, "acc_name": an, "acc_num": anum, "date": now.strftime("%Y-%m-%d %I:%M %p")})
                    update_user(name, data); st.success("Requested!"); st.rerun()
    with c3:
        with st.expander("♻️ REINVEST"):
            r_amt = st.number_input("Reinvest", 1000.0, float(data['wallet']) if data['wallet'] > 1000 else 1000.0, key="r_val")
            if st.button("CONFIRM REINVEST"):
                if data['wallet'] >= r_amt:
                    data['wallet'] -= r_amt
                    data.setdefault('inv', []).append({"amt": r_amt, "start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(name, data); st.success("Done!"); st.rerun()

    # ==========================================
    # BLOCK 7: ACTIVE CYCLES (MATCHING 8833.jpg)
    # ==========================================
    st.markdown("<div class='section-header'>⌛ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    inv_list = data.get('inv', [])
    for idx, t in enumerate(reversed(inv_list)):
        actual_idx = len(inv_list) - 1 - idx
        st_t, et_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
        rem = str(et_t - now).split('.')[0] if now < et_t else "MATURED"
        
        st.markdown(f"""
            <div class='user-box'>
                <div style='color:white; font-size:16px;'>Capital: ₱{t['amt']:,.1f}</div>
                <div class='roi-label'>Accumulated ROI:</div>
                <div class='roi-text'>₱{t.get('accumulated_roi', 0):,.4f}</div>
                <div style='color:#8c8f99; font-size:13px;'>Total to Receive: ₱{t['amt']*0.20:,.2f}</div>
                <br>
                <div style='color:white; font-size:14px;'>
                    <b>Approved:</b> {st_t.strftime('%Y-%m-%d %I:%M %p')}<br>
                    <b>Maturity:</b> {et_t.strftime('%Y-%m-%d %I:%M %p')}
                </div>
                <div style='color:#ff4b4b; font-weight:bold; font-size:15px; margin-top:10px;'>
                    ⌛ TIME REMAINING: {rem}
                </div>
            </div>
        """, unsafe_allow_html=True) 
        
        if now < et_t:
            st.markdown(f"""
                <div class='pull-out-info'>
                    AVAILABLE TO PULL OUT CAPITAL FROM {et_t.strftime('%b %d, %I:%M %p')}<br>
                    TO {(et_t + timedelta(hours=1)).strftime('%I:%M %p')}
                </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"✅ PULL OUT CAPITAL (₱{t['amt']:,})", key=f"pull_{actual_idx}"):
                data['wallet'] += t['amt']
                data['inv'].pop(actual_idx)
                update_user(name, data)
                st.rerun()

    if st.button("LOGOUT"):
        st.session_state.user = None; st.rerun()

# ==========================================
# BLOCK 8: ADMIN BOSS OVERVIEW
# ==========================================
elif st.session_state.is_boss:
    st.title("👑 BOSS OVERVIEW")
    all_u = load_registry()
    for u_n, u_d in all_u.items():
        for tx in u_d.get('tx', []):
            if tx['status'] == "PENDING":
                st.write(f"USER: {u_n} | {tx['type']} | ₱{tx['amt']} | {tx.get('date')}")
                if st.button(f"APPROVE {u_n} {tx['amt']} ##{random.randint(0,999)}"):
                    tx['status'] = "SUCCESSFUL"
                    if tx['type'] == "DEP":
                        u_d.setdefault('inv', []).append({"amt": tx['amt'], "start": datetime.now().isoformat(), "end": (datetime.now() + timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(u_n, u_d); st.rerun()
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
        
