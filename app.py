import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. CONFIG & MOBILE SCROLL FIX ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭", layout="centered")

# CSS to force scrolling on mobile devices
st.markdown("""
<style>
    .main .block-container { max-width: 95%; padding-bottom: 100px; }
    input[type="text"] { text-transform: uppercase; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #0038a8; color: white; font-weight: bold; }
    .logo-text { text-align: center; color: #0038a8; font-weight: 900; font-size: 2em; }
    .info-box { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #0038a8; margin-bottom: 20px; }
    .owner-card { background-color: #f1f5f9; padding: 12px; border-radius: 8px; border-left: 5px solid #0038a8; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGO ---
st.markdown('<p class="logo-text">🇵🇭 BAGONG PILIPINAS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-weight: bold;'>AUTHORIZED STOCK MARKET PORTAL</p>", unsafe_allow_html=True)

# --- 3. DATABASE ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'users_db' not in st.session_state: st.session_state.users_db = []
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'pending_deposits' not in st.session_state: st.session_state.pending_deposits = []

# --- 4. LOGIN ---
if st.session_state.page == "login":
    st.subheader("LOGIN")
    l_name = st.text_input("FULL NAME").upper()
    l_pin = st.text_input("PASSWORD / PIN", type="password")
    
    if st.button("ENTER MARKET"):
        if l_name == "ADMIN" and l_pin == "090807":
            st.session_state.page = "admin"
            st.rerun()
        else:
            user = next((u for u in st.session_state.users_db if u['name'] == l_name and u['pin'] == l_pin), None)
            if user:
                st.session_state.current_user = user
                st.session_state.page = "dashboard"
                st.rerun()
            else: st.error("INVALID CREDENTIALS")
    
    if st.button("NO ACCOUNT? SIGN UP"):
        st.session_state.page = "signup"
        st.rerun()

# --- 5. SIGN UP ---
elif st.session_state.page == "signup":
    st.subheader("CREATE ACCOUNT")
    reg_name = st.text_input("FULL NAME").upper()
    pin1 = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6)
    if st.button("COMPLETE REGISTRATION"):
        if reg_name and len(pin1) == 6:
            st.session_state.users_db.append({"name": reg_name, "pin": pin1, "investments": []})
            st.success("✅ REGISTERED!")
            time.sleep(1)
            st.session_state.page = "login"
            st.rerun()

# --- 6. OWNER ADMIN ---
elif st.session_state.page == "admin":
    st.subheader("👑 OWNER DASHBOARD")
    
    # Summary Metrics
    total_invested = sum(sum(i['amount'] for i in u['investments']) for u in st.session_state.users_db)
    st.metric("PLATFORM TOTAL CAPITAL", f"₱{total_invested:,.2f}")
    
    tab1, tab2 = st.tabs(["👥 INVESTORS", "📥 PENDING"])
    
    with tab1:
        st.write("### List of Active Investors")
        for u in st.session_state.users_db:
            p = sum(i['amount'] for i in u['investments'])
            st.markdown(f"""
            <div class="owner-card">
                <b>Name:</b> {u['name']}<br>
                <b>Principal:</b> ₱{p:,.2f}<br>
                <b>Profit (20%):</b> ₱{p*0.2:,.2f}<br>
                <b>Total Value:</b> ₱{p*1.2:,.2f}
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        if not st.session_state.pending_deposits: st.info("No pending payments.")
        for i, dep in enumerate(st.session_state.pending_deposits):
            st.write(f"**{dep['user']}** | ₱{dep['amount']:,}")
            if st.button("APPROVE", key=f"app_{i}"):
                for u in st.session_state.users_db:
                    if u['name'] == dep['user']: u['investments'].append({"amount": dep['amount']})
                st.session_state.pending_deposits.pop(i)
                st.rerun()

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()

# --- 7. USER DASHBOARD ---
elif st.session_state.page == "dashboard":
    u = st.session_state.current_user
    st.markdown(f"""
    <div class="info-box">
        <h4 style="color:#0038a8; margin-top:0;">📊 INVESTOR INFO</h4>
        <p style="font-size:0.85em;">YOUR EVERY PENNY IS USED TO TRADE IN THE STOCK MARKET OR BLACK MARKET INTERNATIONAL TRADING OF COMMODITIES AND ETC.</p>
    </div>
    """, unsafe_allow_html=True)

    principal = sum(i['amount'] for i in u['investments'])
    st.metric("TOTAL BALANCE", f"₱{principal * 1.2:,.2f}", f"+₱{principal*0.2:,.2f} Interest")

    st.subheader("📥 INVEST")
    amt = st.selectbox("PESO AMOUNT", [500, 1000, 5000, 10000, 50000])
    if st.button(f"INVEST ₱{amt:,}"):
        st.session_state.pending_deposits.append({"user": u['name'], "amount": float(amt)})
        st.success("Request sent to Owner!")

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()
