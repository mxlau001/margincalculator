import streamlit as st
import pandas as pd

# --- STYLING: WHITE THEME & PRECISION BORDERS ---
st.set_page_config(layout="wide", page_title="Pricing Engine")

st.markdown("""
    <style>
    /* Global White Theme */
    .stApp { background-color: white; color: #1E824C; font-family: 'Helvetica', sans-serif; }
    
    /* Settings/Sidebar Border */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #1E824C;
        background-color: white !important;
    }

    /* Input Section Containers */
    [data-testid="stVerticalBlock"] > div { border-radius: 0px; }
    
    /* Boxed Summary Section - wrapping the whole bottom area */
    .summary-container {
        border: 2px solid #1E824C;
        padding: 20px;
        border-radius: 5px;
        margin-top: 30px;
    }
    
    /* Color Overrides */
    h1, h2, h3, h4, p, span, label, div { color: #1E824C !important; }
    
    /* Remove +/- buttons from number inputs */
    button[step="1"], button[step="1000"] { display: none; }
    input[type=number] { -moz-appearance: textfield; }
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC ---
def apply_calculations(df, type="price"):
    df = df.copy()
    df['Growth %'] = df['Tier Max'].pct_change().fillna(0) * 100
    col = 'Price' if type == "price" else 'Rate %'
    df['Discount %'] = df[col].pct_change().fillna(0) * 100
    return df

def get_margin(val, tiers_upper, rates, mode, is_percentage=False):
    if not val or val == 0: return 0
    tiers = [t for t in tiers_upper if t is not None and t > 0]
    adj_rates = [(r / 100) if is_percentage else r for r in rates[:len(tiers)]]
    lowers = [0] + tiers[:-1]
    
    if mode == "Waterfall":
        total = 0
        for i in range(len(tiers)):
            if val > lowers[i]:
                total += (min(val, tiers[i]) - lowers[i]) * adj_rates[i]
        return total
    else: # Top-Tier
        for i in range(len(tiers)):
            if val <= tiers[i]: return val * adj_rates[i]
        return val * (adj_rates[-1] if adj_rates else 0)

# --- SETTINGS SIDEBAR ---
with st.sidebar:
    st.header("SETTINGS")
    calc_mode = st.radio("Calculation Logic", ["Waterfall", "Top-Tier"])
    currency = st.selectbox("Currency Selection", ["AUD", "CNY", "EUR", "GBP", "HKD", "INR", "JPY", "MYR", "NZD", "SGD", "USD"], index=10)
    st.divider()
    if st.button("RESET DEFAULTS"):
        st.rerun()

# --- MAIN UI ---
st.title("PRICING COMPARISON ENGINE")

col_curr, col_prop = st.columns(2)

# Unified Table Configuration
table_config = {
    "Tier Max": st.column_config.NumberColumn("Tier Max", format="%d"),
    "Price": st.column_config.NumberColumn("Price", format="%.2f"),
    "Rate %": st.column_config.NumberColumn("Rate %", format="%.3f%%"),
    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%", disabled=True),
    "Discount %": st.column_config.NumberColumn("Discount %", format="%.1f%%", disabled=True)
}

def render_pricing(label):
    with st.container():
        st.subheader(f"{label.upper()} SETUP")
        
        # Inputs - Note: step=0 and custom CSS removes the +/- buttons
        tx = st.number_input(f"Transactions ({label})", value=4200, step=0, format="%d", key=f"tx_{label}")
        vol = st.number_input(f"Volume ({label})", value=4000000000, step=0, format="%d", key=f"vol_{label}")
        
        st.markdown("#### PROCESSING FEES")
        p_data = pd.DataFrame({"Tier Max": [100000, 500000, 1000000], "Price": [10.0, 9.0, 8.0]})
        p_edit = st.data_editor(
            apply_calculations(p_data, "price"), 
            num_rows="dynamic", # This adds the (+/-) row functionality
            key=f"p_{label}", 
            column_config=table_config
        )
        
        st.markdown("#### ACQUIRING MARKUP")
        a_data = pd.DataFrame({"Tier Max": [300000000, 1000000000, 5000000000], "Rate %": [0.600, 0.492, 0.402]})
        a_edit = st.data_editor(
            apply_calculations(a_data, "rate"), 
            num_rows="dynamic", 
            key=f"a_{label}", 
            column_config=table_config
        )

        p_m = get_margin(tx, p_edit["Tier Max"].tolist(), p_edit["Price"].tolist(), calc_mode)
        a_m = get_margin(vol, a_edit["Tier Max"].tolist(), a_edit["Rate %"].tolist(), calc_mode, is_percentage=True)
        
        return {"total": p_m + a_m, "vol": vol}

with col_curr:
    res_c = render_pricing("Current")

with col_prop:
    res_p = render_pricing("Proposal")

# --- FINAL BOXED COMPARISON ---
# Opening the boxed div
st.markdown('<div class="summary-container">', unsafe_allow_html=True)
st.subheader("FINAL MARGIN COMPARISON")

c1, c2, c3 = st.columns(3)
tr_c = (res_c['total'] / res_c['vol']) if res_c['vol'] > 0 else 0
tr_p = (res_p['total'] / res_p['vol']) if res_p['vol'] > 0 else 0

with c1:
    st.metric(f"TOTAL MARGIN ({currency})", f"{res_p['total']:,.2f}", delta=f"{res_p['total'] - res_c['total']:,.2f}")
with c2:
    st.metric("TAKE RATE", f"{tr_p*100:.4f}%", delta=f"{(tr_p - tr_c)*100:.4f}%")
with c3:
    be_vol = (res_c['total'] / tr_p) if tr_p > 0 else 0
    st.metric("BREAKEVEN VOLUME", f"{be_vol:,.0f}")

st.markdown('</div>', unsafe_allow_html=True) # Closing the boxed div
