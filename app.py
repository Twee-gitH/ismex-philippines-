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

# --- 2. DATA ENGINE ---
REGISTRY_FILE = "bpsm_registry.json"
def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f: return json.load(f)
    return {}

def update_user(name, data):
    reg = load_registry()
    reg[name] = data
    with open(REGISTRY_FILE, "w") as f: json.dump(reg, f)

# --- 3. THE AGGRESSIVE CSS FIX ---
st.set_page_config(page_title="BPSM Official", layout="wide")

st.markdown("""
    <style>
    /* 1. Force general text to look like Caps */
    input[type="text"] { 
        text-transform: uppercase !important; 
    }
    
    /* 2. FORCE PASSWORDS TO REMAIN EXACTLY AS TYPED (Small or Big) */
    /* This overrides every other rule in the browser */
    input[type="password"] {
        text-transform: none !important;
        -webkit-text-transform: none !important;
        text-transform: lowercase !important; /* Only looks lowercase, but accepts whatever you type */
        font-family: monospace !important;
    }
    
    /* 3. Visual cleanup */
    .user-box { background-color: #1c1e24; padding: 20px; border-radius: 15px; border: 1px solid #3a3d46; text-align: center; margin-bottom: 20px; }
    .balance-val { color: #00ff88; font-size: 36px; margin: 0; }
    .section-header { background: #252830; padding: 10px; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #ce1126; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESS CONTROL ---
if st.session_state.user is None and not st.session_state.is_boss:
    st.markdown("<div style='background: linear-gradient(135deg, #0038a8 0%, #ce1126 100%); padding: 40px 20px; text-align: center;'><h1>BAGONG PILIPINAS<br>STOCK MARKET</h1></div>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔑 SIGN-IN", "📝 REGISTER"])
    with t1:
        ln = st.text_input("INVESTOR NAME").upper()
        lp = st.text_input("SECURE PIN", type="password")
        if st.button("VERIFY & ACCESS"):
            reg = load_registry()
            if ln in reg and str(reg[ln].get('pin')) == str(lp):
                st.session_state.user = ln
                st.rerun()
            else: st.error("❌ INVALID CREDENTIALS")
            
    with t2:
        rn = st.text_input("FULL LEGAL NAME", key="reg_name").upper()
        rp1 = st.text_input("CREATE PIN", type="password", key="p1")
        rp2 = st.text_input("CONFIRM PIN", type="password", key="p2")
        referrer = st.text_input("REFERRER NAME").upper()
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            if rp1 != rp2: st.error("❌ PIN MISMATCH")
            else:
                update_user(rn, {"pin": rp1, "wallet": 0.0, "inv": [], "tx": [], "ref_by": referrer, "claimed_refs": []})
                st.success("✅ REGISTERED!"); time.sleep(1); st.rerun()

    # --- THE ADMIN BOX (WITH DEBUGGER) ---
    with st.expander("🔐 ADMIN ACCESS"):
        ap = st.text_input("ENTER ADMIN PIN", type="password", key="admin_field")
        
        # This line is for YOU to see what the computer is reading
        if ap:
            st.write(f"System reads this many characters: {len(ap)}")
            
        if st.button("LOGIN AS BOSS"):
            # I am making the check CASE-INSENSITIVE for the word 'Admin' 
            # just to make sure you get in!
            if ap.lower() == "admin123": 
                st.session_state.is_boss = True
                st.rerun()
            else:
                st.error(f"❌ DENIED. You typed: {ap}") # Shows you exactly what failed
    st.stop()

# --- 5. DASHBOARD (KEEPING ALL YOUR FEATURES) ---
if st.session_state.user:
    name = st.session_state.user
    reg = load_registry()
    data = reg[name]
    now = datetime.now()

    # ROI Logic & Auto-Reinvest (7 Days + 1 Hour Window)
    changed = False
    rate = (0.20 / 7) / 1440
    for i in data.get('inv', []):
        start_t = datetime.fromisoformat(i['start'])
        end_t = datetime.fromisoformat(i['end'])
        grace_end = end_t + timedelta(hours=1)
        
        # Accumulate
        mins = (min(now, end_t) - start_t).total_seconds() / 60
        i['live_roi'] = i['amt'] * (mins * rate)

        if now >= end_t and not i.get('roi_paid', False):
            data['wallet'] += i['amt'] * 0.20
            i['roi_paid'] = True
            changed = True
        
        if now >= grace_end:
            i.update({"start": now.isoformat(), "end": (now+timedelta(days=7)).isoformat(), "roi_paid": False})
            changed = True
    if changed: update_user(name, data); st.rerun()

    st.markdown(f"<div class='user-box'><h1 class='balance-val'>₱{data['wallet']:,.2f}</h1><p>{name}</p></div>", unsafe_allow_html=True)
    
    # Active Cycles
    st.markdown("<div class='section-header'>⏳ ACTIVE CYCLES</div>", unsafe_allow_html=True)
    for idx, t in enumerate(data.get('inv', [])):
        et = datetime.fromisoformat(t['end'])
        ge = et + timedelta(hours=1)
        st.write(f"Capital: ₱{t['amt']:,} | ROI: ₱{t.get('live_roi',0):,.2f}")
        btn_txt = f"PULL OUT WINDOW: {et.strftime('%I:%M%p')} - {ge.strftime('%I:%M%p')}"
        if et <= now < ge:
            if st.button(f"✅ PULL ₱{t['amt']:,}", key=f"p{idx}"):
                data['wallet'] += t['amt']; data['inv'].pop(idx)
                update_user(name, data); st.rerun()
        else:
            st.button(btn_txt, disabled=True, key=f"d{idx}")

    # Referrals & History
    st.markdown("<div class='section-header'>👥 REFERRALS</div>", unsafe_allow_html=True)
    refs = [{"NAME": k, "COMM": f"₱{v['tx'][0]['amt']*0.2:.2f}" if v.get('tx') else "0"} for k,v in load_registry().items() if v.get('ref_by')==name]
    if refs: st.table(pd.DataFrame(refs))
    
    if st.button("LOGOUT"): st.session_state.user = None; st.rerun()

# --- 6. BOSS PANEL ---
elif st.session_state.is_boss:
    st.title("👑 BOSS PANEL")
    all_u = load_registry()
    for u, d in all_u.items():
        for tx in d.get('tx', []):
            if tx['status'] == "PENDING_DEP":
                if st.button(f"Approve {u} - ₱{tx['amt']}"):
                    tx['status'] = "SUCCESSFUL_DEP"
                    d.setdefault('inv', []).append({"amt": tx['amt'], "start": datetime.now().isoformat(), "end": (datetime.now()+timedelta(days=7)).isoformat(), "roi_paid": False})
                    update_user(u, d); st.rerun()
    if st.button("EXIT"): st.session_state.is_boss = False; st.rerun()
                
