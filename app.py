import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. APP CONFIG & STYLE ---
st.set_page_config(page_title="BP Market", page_icon="🇵🇭")

st.markdown("""
    <style>
    .stApp { margin-top: 50px; }
    /* Only text inputs are forced to Upper Case now */
    input[type="text"] { text-transform: uppercase; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #0038a8;
        color: white;
        font-weight: bold;
        border: none;
        margin-top: 10px;
    }
    .deposit-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .timer-text { color: #f59e0b; font-weight: bold; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE "MEMORY" (SESSION STATE) ---
if 'deposits' not in st.session_state:
    st.session_state.deposits = []
if 'page' not in st.session_state:
    st.session_state.page = "signup"
if 'user_pin' not in st.session_state:
    st.session_state.user_pin = ""

# --- 3. CALCULATIONS ---
total_principal = sum(d['amount'] for d in st.session_state.deposits)
total_profit = sum(d['amount'] * 0.20 for d in st.session_state.deposits)
total_balance = total_principal + total_profit

# --- 4. SIGNUP PAGE ---
if st.session_state.page == "signup":
    st.markdown("<h2 style='text-align: center;'>🇵🇭 INVESTOR SIGN UP</h2>", unsafe_allow_html=True)
    full_name = st.text_input("FULL NAME").upper()
    
    st.markdown("---")
    # PIN logic: max 6 chars, numeric only
    reg_pin = st.text_input("CREATE 6-DIGIT PIN", type="password", max_chars=6, help="Numbers only")
    st.caption("⚠️ MUST BE EXACTLY 6 DIGIT NUMBERS")

    if st.button("CREATE SECURE ACCOUNT"):
        if full_name and len(reg_pin) == 6 and reg_pin.isdigit():
            st.session_state.user_name = full_name
            st.session_state.user_pin = reg_pin
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("PLEASE PROVIDE FULL NAME AND A 6-DIGIT NUMERIC PIN")

# --- 5. DASHBOARD PAGE ---
elif st.session_state.page == "dashboard":
    st.markdown(f"### MABUHAY, {st.session_state.user_name}!")
    
    col1, col2 = st.columns(2)
    col1.metric("TOTAL BALANCE", f"₱{total_balance:,.2f}")
    col2.metric("EXPECTED PROFIT", f"₱{total_profit:,.2f}", delta="20% DAILY")

    st.markdown("---")
    
    # --- DEPOSIT SECTION ---
    st.subheader("📥 NEW INVESTMENT")
    amounts = [100, 500, 1000, 5000, 10000, 20000, 30000, 50000]
    selected_amt = st.selectbox("CHOOSE PESO AMOUNT", amounts)
    
    if st.button(f"INVEST ₱{selected_amt:,}"):
        new_dep = {
            "amount": float(selected_amt),
            "start_time": datetime.now(),
            "release_time": datetime.now() + timedelta(hours=24),
            "profit": float(selected_amt) * 0.20
        }
        st.session_state.deposits.append(new_dep)
        st.success(f"₱{selected_amt:,} ADDED TO YOUR PORTFOLIO!")
        st.rerun()

    # --- INDIVIDUAL DEPOSITS + COUNTDOWN ---
    st.markdown("---")
    st.subheader("⏳ ACTIVE INVESTMENTS")
    if not st.session_state.deposits:
        st.write("No active investments.")
    else:
        for d in st.session_state.deposits:
            # Calculate remaining time
            remaining = d['release_time'] - datetime.now()
            if remaining.total_seconds() > 0:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                timer_display = f"{hours}h {minutes}m remaining"
            else:
                timer_display = "✅ PROFIT READY"

            st.markdown(f"""
            <div class="deposit-card">
                <b>Investment: ₱{d['amount']:,}</b><br>
                <span style="color: green;">+ ₱{d['profit']:,} (20% Profit)</span><br>
                <span class="timer-text">🕒 {timer_display}</span>
            </div>
            """, unsafe_allow_html=True)

    # --- WITHDRAWAL SECTION ---
    st.markdown("---")
    st.subheader("📤 WITHDRAW")
    st.caption("MINIMUM WITHDRAWAL: ₱500.00")
    withdraw_amt = st.number_input("ENTER PESO AMOUNT", min_value=0.0)
    
    # Security Check
    confirm_pin = st.text_input("ENTER 6-DIGIT PIN TO WITHDRAW", type="password", max_chars=6)
    
    if st.button("SUBMIT WITHDRAWAL REQUEST"):
        if total_balance < 500:
            st.error("⚠️ BALANCE MUST BE AT LEAST ₱500.00")
        elif withdraw_amt < 500:
            st.error("⚠️ MINIMUM WITHDRAWAL IS ₱500.00")
        elif confirm_pin != st.session_state.user_pin:
            st.error("❌ INCORRECT PIN. ACCESS DENIED.")
        elif withdraw_amt > total_balance:
            st.error("⚠️ INSUFFICIENT FUNDS.")
        else:
            st.success("✅ PIN VERIFIED. WITHDRAWAL REQUEST SENT TO ADMIN.")

    if st.button("LOGOUT"):
        st.session_state.page = "signup"
        st.rerun()
        
