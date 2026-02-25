import streamlit as st
import pandas as pd
import json

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Pricing Proposal Tool v2")

# --- SESSION STATE INITIALIZATION (Save Scenario Logic) ---
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {}

# --- CONSTANTS ---
CURRENCIES = ["AUD", "CNY", "EUR", "GBP", "HKD", "INR", "JPY", "MYR", "NZD", "SGD", "USD"]

# --- MATH LOGIC ---
def calculate_margin(val, tiers_upper, rates, mode):
    if not val or val == 0: return 0
    tiers = [t for t in tiers_upper if t is not None and t > 0]
    prices = rates[:len(tiers)]
    lowers = [0] + tiers[:-1]
    
    if mode == "Waterfall":
        total_margin = 0
        for i in range(len(tiers)):
            if val > lowers[i]:
                applicable_amt = min(val, tiers[i]) - lowers[i]
                total_margin += applicable_amt * prices[i]
        return total_margin
    else: # Top-Tier
        for i in range(len(tiers)):
            if val <= tiers[i]:
                return val * prices[i]
        return val * prices[-1]

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛠 Control Panel")
    calc_mode = st.selectbox("Calculation Method", ["Waterfall", "Top-Tier"])
    base_currency = st.selectbox("Display Currency", CURRENCIES, index=2)
    fx_rate = st.number_input(f"FX Rate (1 {base_currency} = X Local)", value=150.0)
    
    st.divider()
    st.subheader("💾 Saved Scenarios")
    scenario_name = st.text_input("Scenario Name", placeholder="e.g. Q4 Growth Plan")
    
    if st.button("Save Current View"):
        if scenario_name:
            # Saving current state to session
            st.session_state.scenarios[scenario_name] = {
                "mode": calc_mode,
                "fx": fx_rate
            }
            st.success(f"Saved '{scenario_name}'")
        else:
            st.error("Please enter a name")

    if st.session_state.scenarios:
        selected_old = st.selectbox("Load Previous Scenario", list(st.session_state.scenarios.keys()))
        if st.button("Load"):
            st.info(f"Loaded {selected_old}. (Adjusting Global Settings...)")

# --- MAIN UI ---
st.title("Pricing & Margin Impact Tool")

col_curr, col_prop = st.columns(2)

def render_pricing_column(key_suffix):
    with st.container(border=True):
        st.subheader(f"{key_suffix} Configuration")
        
        # 1. Processing
        st.markdown("#### 💳 Processing Fees")
        tx = st.number_input("Total Transactions", value=4200, key=f"tx_{key_suffix}")
        proc_df = pd.DataFrame({"Tier Max": [100000, 500000, 1000000], "Price": [10.0, 9.0, 8.0]})
        proc_edited = st.data_editor(proc_df, key=f"ed_proc_{key_suffix}", num_rows="dynamic")
        
        # 2. Acquiring
        st.markdown("#### 📈 Acquiring Markup")
        vol = st.number_input("Monthly Volume", value=4000000000, key=f"vol_{key_suffix}")
        acq_df = pd.DataFrame({"Tier Max": [300000000, 1000000000, 5000000000], "Rate %": [0.006, 0.005, 0.004]})
        acq_edited = st.data_editor(acq_df, key=f"ed_acq_{key_suffix}", num_rows="dynamic")

        # Calculations
        p_marg = calculate_margin(tx, proc_edited["Tier Max"].tolist(), proc_edited["Price"].tolist(), calc_mode)
        a_marg = calculate_margin(vol, acq_edited["Tier Max"].tolist(), acq_edited["Rate %"].tolist(), calc_mode)
        
        total_local = p_marg + a_marg
        total_base = total_local / fx_rate
        take_rate = (total_local / vol) if vol > 0 else 0
        
        return {"total_base": total_base, "take_rate": take_rate, "total_local": total_local}

with col_curr:
    res_c = render_pricing_column("Current")

with col_prop:
    res_p = render_pricing_column("Proposal")

# --- FOOTER SUMMARY ---
st.divider()
st.header("Final Comparison")
c1, c2, c3 = st.columns(3)

with c1:
    delta_val = res_p['total_base'] - res_c['total_base']
    st.metric(f"Margin Delta ({base_currency})", f"{res_p['total_base']:,.2f}", delta=f"{delta_val:,.2f}")

with c2:
    tr_delta = (res_p['take_rate'] - res_c['take_rate']) * 100
    st.metric("Take Rate Impact", f"{res_p['take_rate']*100:.4f}%", delta=f"{tr_delta:.4f}%")

with c3:
    annual_impact = delta_val * 12
    st.metric("Annualized Impact", f"{res_p['total_base']*12:,.2f}", delta=f"{annual_impact:,.2f}")

if delta_val < 0:
    st.warning("⚠️ Warning: This proposal results in a margin reduction compared to current pricing.")
else:
    st.balloons()
    st.success("✅ Profit Improvement detected in this proposal.")
