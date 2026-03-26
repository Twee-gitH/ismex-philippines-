import streamlit as st

# --- 1. SETTINGS ---
st.set_page_config(page_title="BP Market")

# --- 2. DATABASE ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'users' not in st.session_state: st.session_state.users = []
if 'pending' not in st.session_state: st.session_state.pending = []

# --- 3. LOGIN PAGE ---
if st.session_state.page == "login":
    st.header("🇵🇭 BP MARKET LOGIN")
    name = st.text_input("FULL NAME").upper()
    pin = st.text_input("PIN / PASSWORD", type="password")
    
    if st.button("ENTER"):
        # OWNER LOGIN (Your Secret Code)
        if name == "ADMIN" and pin == "090807":
            st.session_state.page = "admin"
            st.rerun()
        # USER LOGIN
        user = next((u for u in st.session_state.users if u['n'] == name and u['p'] == pin), None)
        if user:
            st.session_state.cur_user = user
            st.session_state.page = "dash"
            st.rerun()
        else:
            st.error("Invalid Name or PIN")
            
    if st.button("CREATE ACCOUNT"):
        st.session_state.page = "signup"
        st.rerun()

# --- 4. SIGN UP PAGE ---
elif st.session_state.page == "signup":
    st.header("SIGN UP")
    new_name = st.text_input("NAME").upper()
    new_pin = st.text_input("6-DIGIT PIN", type="password", max_chars=6)
    if st.button("REGISTER"):
        if new_name and len(new_pin) == 6:
            st.session_state.users.append({'n': new_name, 'p': new_pin, 'bal': 0})
            st.success("Registered! Please Login.")
            st.session_state.page = "login"
            st.rerun()

# --- 5. OWNER ADMIN PAGE ---
elif st.session_state.page == "admin":
    st.header("👑 OWNER DASHBOARD")
    st.write("### Pending Approvals")
    if not st.session_state.pending:
        st.info("No pending investments.")
    for i, d in enumerate(st.session_state.pending):
        st.write(f"User: {d['u']} | Amount: ₱{d['a']:,}")
        if st.button(f"APPROVE PAYMENT {i}"):
            for u in st.session_state.users:
                if u['n'] == d['u']: u['bal'] += d['a']
            st.session_state.pending.pop(i)
            st.rerun()
    
    st.write("---")
    st.write("### Active Investors List")
    for u in st.session_state.users:
        st.write(f"Name: {u['n']} | Total: ₱{u['bal'] * 1.2:,.2f}")
    
    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()

# --- 6. USER DASHBOARD ---
elif st.session_state.page == "dash":
    u = st.session_state.cur_user
    st.header(f"Welcome, {u['n']}")
    # Your specific investment pitch
    st.info("YOUR EVERY PENNY IS USED TO TRADE IN THE STOCK MARKET OR BLACK MARKET INTERNATIONAL TRADING OF COMMODITIES AND ETC.")
    
    # Shows balance + 20% interest
    st.metric("TOTAL BALANCE", f"₱{u['bal'] * 1.2:,.2f}", f"+₱{u['bal']*0.2:,.2f} Interest")
    
    amt = st.number_input("Amount to Invest", min_value=100, step=100)
    if st.button("PROCEED TO INVEST"):
        st.session_state.pending.append({'u': u['n'], 'a': float(amt)})
        st.success("Payment request sent to Admin!")

    if st.button("LOGOUT"):
        st.session_state.page = "login"
        st.rerun()
