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
    /* ... your existing CSS ... */
    
    /* THIS FORCES ALL TEXT INPUTS TO LOOK LIKE CAPS LOCK IS ON */
    input {
        text-transform: uppercase;
    }
    
    /* Optional: If you want placeholders to stay normal but typing to be Caps */
    input::placeholder {
        text-transform: none;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 4. ACCESS CONTROL (ENHANCED REFERRAL & PIN RULES) ---
if st.session_state.user is None and not st.session_state.is_boss:
    # CSS to force ALL-CAPS visually in the input boxes
    st.markdown("""
        <style>
        input { text-transform: uppercase; }
        input[type="password"] { text-transform: none; } 
        </style>
        """, unsafe_allow_html=True)

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
            else: st.error("❌ INVALID CREDENTIALS")
            
    with t2:
        st.warning("⚠️ **IMPORTANT:** PLEASE INPUT ONLY YOUR LEGAL FIRST NAME AND LAST NAME.")
        rn = st.text_input("FULL LEGAL NAME (LEGAL FIRST NAME & LAST NAME ONLY)", key="reg_name").upper()
        
        st.info("ℹ️ **PIN SECURITY:** 6-DIGIT PIN MUST BE NUMBERS ONLY. LETTERS OR SPECIAL CHARACTERS ARE NOT ALLOWED.")
        rp1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6, key="reg_pin1")
        rp2 = st.text_input("CONFIRM 6-DIGIT PIN", type="password", max_chars=6, key="reg_pin2")
        
        # Updated Referral Label and Info
        st.error("🚨 **REFERRAL RULE:** ONLY ACTIVE INVESTORS ARE ALLOWED TO REFER NEW USERS.")
        referrer = st.text_input("REFERRER NAME (ACTIVE INVESTOR ONLY)", key="reg_ref").upper()
        
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            final_name = rn.strip().upper()
            name_parts = final_name.split()
            
            # Validation Checks
            if len(name_parts) < 2:
                st.error("❌ PLEASE INPUT BOTH YOUR LEGAL FIRST NAME AND LAST NAME.")
            elif not rp1.isdigit():
                st.error("❌ PIN ERROR: NUMBERS ONLY! LETTERS AND SPECIAL CHARACTERS ARE NOT ALLOWED.")
            elif rp1 != rp2:
                st.error("❌ PINS DO NOT MATCH. PLEASE RETYPE YOUR PIN.")
            elif len(rp1) != 6:
                st.error("❌ PIN MUST BE EXACTLY 6 DIGITS.")
            elif not referrer or referrer not in reg:
                st.error("❌ VALID REFERRER REQUIRED.")
            elif not reg[referrer].get('inv'):
                st.error(f"❌ {referrer} IS NOT AN ACTIVE INVESTOR. ONLY ACTIVE INVESTORS CAN REFER.")
            elif final_name in reg:
                st.error("❌ THIS LEGAL NAME IS ALREADY REGISTERED.")
            else:
                update_user(final_name, {
                    "pin": rp1, "wallet": 0.0, "inv": [], "tx": [], 
                    "ref_by": referrer, "claimed_refs": []
                })
                st.success("✅ ACCOUNT CREATED SUCCESSFULLY!"); time.sleep(1.5); st.rerun()
    st.stop()
    
    
    

# --- 5. INVESTOR PORTAL ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # --- AUTO-PROCESSOR ---
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
                data_changed = True
        except: continue
    
    if data_changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><p style='color:#8c8f99;'>WITHDRAWABLE BALANCE</p><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p style='color:#8c8f99;'>Account: {name}</p></div>", unsafe_allow_html=True)

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

        st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
        if not data.get('inv'): st.write("No active interest running.")
        else:
            for idx, t in enumerate(reversed(data['inv'])):
                actual_idx = len(data['inv']) - 1 - idx
                try:
                    start_t, end_t = datetime.fromisoformat(t['start']), datetime.fromisoformat(t['end'])
                    exact_roi = t['amt'] * 0.20
                    st.markdown(f"<div style='background:#1c1e24; padding:15px; border-radius:15px; border:1px solid #3a3d46; margin-bottom:10px;'><div class='meta-text'>📅 DEPOSIT: {start_t.strftime('%Y-%m-%d %I:%M %p')}</div><div class='meta-text'>🏁 MATURITY: {end_t.strftime('%Y-%m-%d %I:%M %p')}</div><div style='display:flex; justify-content:space-between; margin-top:5px;'><span style='font-weight:bold;'>Capital: ₱{t['amt']:,}</span><span class='roi-text'>TOTAL ROI: ₱{exact_roi:,.2f}</span></div></div>", unsafe_allow_html=True)
                    if now < end_t:
                        rem = end_t - now
                        st.button(f"LOCKED UNTIL MATURITY (⏳ {str(rem).split('.')[0]})", key=f"l_{actual_idx}", disabled=True)
                    elif end_t <= now < (end_t + timedelta(hours=1)):
                        grace_rem = (end_t + timedelta(hours=1)) - now
                        st.markdown(f"<div class='timer-alert'>⚠️ 1-HOUR PULL-OUT TIMER: {str(grace_rem).split('.')[0]}</div>", unsafe_allow_html=True)
                        if st.button(f"✅ PULL CAPITAL (₱{t['amt']:,})", key=f"pull_{actual_idx}"):
                            data['wallet'] += t['amt']
                            data['inv'].pop(actual_idx)
                            data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "CAPITAL PULL-OUT", "amt": t['amt'], "status": "SUCCESSFUL"})
                            update_user(name, data); st.rerun()
                except: continue

        st.markdown("<div class='section-header'>👥 MY REFERRALS</div>", unsafe_allow_html=True)
        reg_all = load_registry()
        my_refs_list = []
        if 'claimed_refs' not in data: data['claimed_refs'] = []
        
        for u_name, u_info in reg_all.items():
            if u_info.get('ref_by') == name:
                first_dep_amt = 0
                for tx in u_info.get('tx', []):
                    if tx['status'] == "SUCCESSFUL_DEP":
                        first_dep_amt = tx['amt']
                        break
                is_investor = first_dep_amt > 0
                already_paid = u_name in data['claimed_refs']
                status_text = "✅ PAID" if already_paid else (f"₱{first_dep_amt:,.2f}" if is_investor else "NOT ACTIVE")
                my_refs_list.append({"INVITEE": u_name, "1ST DEPOSIT": status_text, "BONUS (20%)": 0 if already_paid else (first_dep_amt * 0.20), "CLAIMABLE": is_investor and not already_paid})
        
        if my_refs_list:
            st.table(pd.DataFrame(my_refs_list).drop(columns=['CLAIMABLE']))
            total_pending_bonus = sum([r["BONUS (20%)"] for r in my_refs_list if r["CLAIMABLE"]])
            if total_pending_bonus > 0:
                st.write(f"### Available Bonus: ₱{total_pending_bonus:,.2f}")
                if st.button("🎁 CLAIM REFERRAL BONUSES"):
                    newly_claimed = [r["INVITEE"] for r in my_refs_list if r["CLAIMABLE"]]
                    data['claimed_refs'].extend(newly_claimed)
                    data['wallet'] += total_pending_bonus
                    data.setdefault('tx', []).append({"date": now.strftime("%Y-%m-%d %H:%M"), "type": "REFERRAL BONUS", "amt": total_pending_bonus, "status": "SUCCESSFUL"})
                    update_user(name, data); st.success("Bonus added!"); time.sleep(1); st.rerun()
        else: st.info("No invitees found.")

        st.markdown("<div class='section-header'>📜 HISTORY</div>", unsafe_allow_html=True)
        for t in reversed(data.get('tx', [])):
            st.write(f"{t['date']} | {t['type']} | ₱{t['amt']:,} | {t['status']}")

    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

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
            
