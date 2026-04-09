import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
import json

# 1. DATABASE CONNECTION WITH MOBILE-FRIENDLY ERROR HANDLING
try:
    if "firebase" in st.secrets:
        # We manually clean the private key to prevent TOML formatting crashes
        raw_key = st.secrets["firebase"]["private_key"]
        fixed_key = raw_key.replace("\\n", "\n")
        
        creds_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": fixed_key,
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=creds)
    else:
        st.error("MISSING SECRETS: Go to Settings > Secrets and add your [firebase] block.")
except Exception as e:
    st.error(f"DATABASE CRASH: {e}")

# Logic Helpers
def load_registry():
    try:
        users_ref = db.collection("investors")
        return {doc.id: doc.to_dict() for doc in users_ref.stream()}
    except: return {}

def update_user(name, data):
    db.collection("investors").document(name).set(data)

# State initialization
for key, val in [('page','ad'), ('user',None), ('is_boss',False), ('admin_mode',False), ('action_type',None)]:
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. UI STYLES (WRAPPED & CLEAN)
# ==========================================
st.set_page_config(page_title="ISMEX Official", layout="wide")

st.markdown("""
    <style>
    /* HIDE STREAMLIT BRANDING & DEVELOPER INFO */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* REMOVE PADDING AT THE TOP */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    /* APP BACKGROUND & TEXT */
    .stApp { 
        background-color: #0e1117 !important; 
        color: white !important; 
    }

    /* CUSTOM BUTTONS */
    div.stButton > button {
        background-color: #1c1e26 !important; 
        color: #ffffff !important;
        border: 2px solid #333 !important; 
        border-radius: 8px !important;
        font-weight: bold !important; 
        width: 100% !important;
    }

    /* DASHBOARD CARDS */
    .hist-card { 
        background: #1c1e26; 
        padding: 15px; 
        border-radius: 5px; 
        margin-bottom: 8px; 
        border-left: 5px solid #00ff88; 
    }
    
    .balance-box { 
        background: #1c1e26; 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #333; 
        margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)


# Handle Referrals from URL
if "ref" in st.query_params:
    st.session_state.url_ref = st.query_params["ref"].replace("+", " ").upper().strip()
current_ref = st.session_state.get("url_ref", "")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; }
    .stApp { background-color: #0e1117 !important; color: white !important; }
    div.stButton > button {
        background-color: #1c1e26 !important; color: #ffffff !important;
        border: 2px solid #333 !important; border-radius: 8px !important;
        font-weight: bold !important; width: 100% !important;
    }
    .hist-card { background: #1c1e26; padding: 15px; border-radius: 5px; margin-bottom: 8px; border-left: 5px solid #00ff88; }
    .roi-text { color: #00ff88; font-weight: bold; float: right; font-size: 18px; }
    .balance-box { background: #1c1e26; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. ADMIN PANEL LOGIC
if st.session_state.is_boss:
    st.title("👑 ADMIN CONTROL")
    if st.button("EXIT ADMIN"): st.session_state.is_boss = False; st.rerun()
    
    reg = load_registry()
    for user, u_data in reg.items():
        pending = u_data.get('pending_actions', [])
        for idx, act in enumerate(list(pending)):
            with st.expander(f"{act['type']} - {user} - ₱{act.get('amount',0):,.2f}"):
                if act['type'] == "WITHDRAW":
                    st.warning(f"BANK: {act.get('bank')} | ACCT: {act.get('acct_num')} | NAME: {act.get('acct_name')}")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", key=f"a_{user}_{idx}"):
                    if act['type'] == "DEPOSIT":
                        u_data.setdefault('inv', []).append({"amount": act['amount'], "start_time": datetime.now().isoformat()})
                    u_data.setdefault('history', []).append({"type": act['type'], "amount": act['amount'], "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "status": "CONFIRMED"})
                    u_data['pending_actions'].pop(idx)
                    update_user(user, u_data); st.rerun()
                if c2.button("❌ REJECT", key=f"r_{user}_{idx}"):
                    if act['type'] == "WITHDRAW": u_data['wallet'] = u_data.get('wallet', 0.0) + act['amount']
                    u_data['pending_actions'].pop(idx); update_user(user, u_data); st.rerun()

# ==========================================
# 4. THE "PRESS HERE" LANDING & AUTH SYSTEM
# ==========================================

# 1. Capture the Referral IMMEDIATELY (Keep this at the top of this block)
if "ref" in st.query_params:
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# 2. Logic to switch between the "Press Here" page and the actual Login/Register forms
if st.session_state.user:
    # This is where your existing Dashboard code starts
    pass 

elif st.session_state.page == "auth":
    # The actual Login and Register Tabs
    st.markdown("### ACCOUNT ACCESS")
    tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
    
    with tab1:
        u_log = st.text_input("FULL NAME", key="l_u").upper().strip()
        p_log = st.text_input("PIN", type="password", key="l_p")
        if st.button("ENTER ISMEX"):
            reg = load_registry()
            if u_log in reg and str(reg[u_log]['pin']) == str(p_log):
                st.session_state.user = u_log
                st.rerun()
            else:
                st.error("Invalid Name or PIN")

    with tab2:
        # Shows the friend's name caught from the referral link
        inviter = st.session_state.get('captured_ref', 'OFFICIAL')
        st.info(f"🤝 Invited by: {inviter}")
        
        new_u = st.text_input("YOUR FULL NAME (FIRST MIDDLE LAST)").upper().strip()
        new_p = st.text_input("SET 4-DIGIT PIN", type="password", max_chars=4)
        
        if st.button("CREATE ACCOUNT"):
            reg = load_registry()
            # STRICT RULE: Block duplicate names
            if new_u in reg:
                st.error("SYSTEM ERROR: THIS NAME IS ALREADY AN INVESTOR!")
            elif len(new_u) < 5:
                st.warning("Please enter your complete full name.")
            elif not new_p:
                st.warning("Please set a PIN.")
            else:
                # Add new user to Firestore
                update_user(new_u, {
                    "pin": new_p,
                    "wallet": 0.0,
                    "ref_by": inviter,
                    "inv": [],
                    "history": [],
                    "pending_actions": []
                })
                st.success("Registration Successful! Please switch to the LOGIN tab.")
    
    if st.button("← BACK TO HOME"):
        st.session_state.page = "landing"
        st.rerun()

else:
    # THE MAIN LANDING SCREEN (WRAPPED UI)
    st.title("ISMEX PHILIPPINES 📊")
    st.write("International Stock Market Exchange")
    
    # Your specific "Press Here" button
    if st.button("🚀 PRESS HERE TO REGISTER OR LOG IN", use_container_width=True):
        st.session_state.page = "auth"
        st.rerun()
    
    # Hidden Admin Entry (Optional)
    with st.expander(" "):
        if st.text_input("Key", type="password") == "0102030405":
            st.session_state.is_boss = True
            st.rerun()
            
    # --- INVESTMENTS & REFERRALS ---
    st.markdown("### 🤝 YOUR REFERRAL LINK")
    st.code(f"https://ismex-philippines.streamlit.app/?ref={user_display.replace(' ', '+')}")

    st.markdown("### 🚀 ACTIVE CAPITALS")
    active = data.get('inv', [])
    if not active: st.info("No active investments.")
    for idx, a in enumerate(reversed(active)):
        start = datetime.fromisoformat(a['start_time'])
        end = start + timedelta(days=7)
        elapsed = (datetime.now() - start).total_seconds()
        prog = min(1.0, elapsed / (7*86400))
        roi = a['amount'] * 1.20
        
        st.markdown(f"<div class='hist-card'><span class='roi-text'>ROI: ₱{roi:,.2f}</span>CAPITAL: ₱{a['amount']:,.2f}</div>", unsafe_allow_html=True)
        st.progress(prog)
        if datetime.now() >= end:
            if st.button(f"📥 PULL OUT ₱{roi:,.2f}", key=f"po_{idx}"):
                data['wallet'] = wallet + roi
                active.pop(len(active)-1-idx)
                update_user(st.session_state.user, data); st.rerun()

    st.markdown("### 📜 HISTORY")
    for h in reversed(data.get('history', [])):
        st.write(f"✅ {h.get('type')} - ₱{h.get('amount',0):,.2f} | {h.get('date')}")

# ==========================================
# 5. LANDING, LOGIN & REFERRAL CAPTURE
# ==========================================

# 1. Capture the Referral IMMEDIATELY before doing anything else
if "ref" in st.query_params:
    # This saves the referral name even if the URL changes later
    st.session_state["captured_ref"] = st.query_params["ref"].replace("+", " ").upper().strip()

# 2. Page Logic
if st.session_state.page == "login":
    st.title("ACCESS PORTAL")
    
    # Show the captured referral so the user knows who invited them
    if "captured_ref" in st.session_state:
        st.success(f"🤝 Invited by: {st.session_state['captured_ref']}")
    
    u = st.text_input("FULL NAME").upper().strip()
    p = st.text_input("PIN", type="password")
    
    if st.button("LOGIN"):
        reg = load_registry()
        if u in reg and str(reg[u]['pin']) == str(p):
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Incorrect Name or PIN")
            
    if st.button("BACK"):
        st.session_state.page = "ad"
        st.rerun()
else:
    st.title("ISMEX PHILIPPINES 📊")
    if st.button("🚀 GET STARTED / LOGIN", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    
    col_a, col_b = st.columns([0.1, 0.9])
    if col_a.button("⛔"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    if st.session_state.admin_mode:
        if st.text_input("Admin Key", type="password") == "0102030405":
            st.session_state.is_boss = True
            st.rerun()
            
