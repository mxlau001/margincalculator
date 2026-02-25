import streamlit as st
import pandas as pd

# --- STYLING: WHITE/GREY/GREEN THEME ---
st.set_page_config(layout="wide", page_title="Margin Calculator")

st.markdown("""
    <style>
    .stApp { background-color: white; color: #1E824C; font-family: 'Courier New', Courier, monospace; }
    [data-testid="stVerticalBlock"] > div:nth-child(1) { background-color: #f2f2f2; border-radius: 5px; }
    .summary-box { border: 2px solid #1E824C; padding: 20px; border-radius: 10px; background-color: white; }
    h1, h2, h3, h4, p, span, label { color: #1E824C !important; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- MATH LOGIC ---
def calculate_metrics(df, type="price"):
    df = df.copy()
    df['Growth %'] = df['Tier Max'].pct_change().fillna(0) * 100
    df['Discount %'] = (df['Price' if type == "price" else 'Rate %'].pct_change().fillna(0)) * 100
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
        return val * adj_rates[-1]

# --- SIDEBAR RESET ---
with st.sidebar:
    st.header("CONTROLS")
    if st.button("RESET TO DEFAULTS"):
        st.rerun()

# --- APP LAYOUT ---
st.title("PRICING COMPARISON ENGINE")

col_curr, col_prop = st.columns(2)

def render_section(label):
    with st.container():
        st.subheader(f"{label.upper()} SETUP")
        
        # Formatted Inputs
        tx = st.number_input(f"Transactions ({label})", value=4200, step=1, format="%d", key=f"tx_{label}")
        vol = st.number_input(f"Volume ({label})", value=4000000000, step=1000, format="%d", key=f"vol_{label}")
        
        # Config for tables to prevent long lines
        col_cfg = {
            "Tier Max": st.column_config.NumberColumn("Tier Max", format="%d"),
            "Price": st.column_config.NumberColumn("Price", format="%.2f"),
            "Rate %": st.column_config.NumberColumn("Rate %", format="%.3f%%"),
            "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
            "Discount %": st.column_config.NumberColumn("Discount %", format="%.1f%%")
        }

        st.markdown("#### PROCESSING FEES")
        p_data = pd.DataFrame({"Tier Max": [100000, 500000, 1000000], "Price": [10.0, 9.0, 8.0]})
        p_edit = st.data_editor(calculate_metrics(p_data, "price"), num_rows="dynamic", key=f"p_{label}", column_config=col_cfg)
        
        st.markdown("#### ACQUIRING MARKUP")
        a_data = pd.DataFrame({"Tier Max": [300000000, 1000000000, 5000000000], "Rate %": [0.600, 0.492, 0.402]})
        a_edit = st.data_editor(calculate_metrics(a_data, "rate"), num_rows="dynamic", key=f"a_{label}", column_config=col_cfg)

        p_m = get_margin(tx, p_edit["Tier Max"].tolist(), p_edit["Price"].tolist(), "Waterfall")
        a_m = get_margin(vol, a_edit["Tier Max"].tolist(), a_edit["Rate %"].tolist(), "Waterfall", is_percentage=True)
        
        return {"total": p_m + a_m, "vol": vol}

with col_curr:
    res_c = render_section("Current")

with col_prop:
    res_p = render_section("Proposal")

# --- FINAL BOXED COMPARISON ---
st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("FINAL MARGIN COMPARISON")

c1, c2, c3 = st.columns(3)
tr_c = (res_c['total'] / res_c['vol']) if res_c['vol'] > 0 else 0
tr_p = (res_p['total'] / res_p['vol']) if res_p['vol'] > 0 else 0

with c1:
    st.metric("TOTAL MARGIN (LOCAL)", f"{res_p['total']:,.2f}", delta=f"{res_p['total'] - res_c['total']:,.2f}")
with c2:
    st.metric("TAKE RATE", f"{tr_p*100:.4f}%", delta=f"{(tr_p - tr_c)*100:.4f}%")
with c3:
    be_vol = (res_c['total'] / tr_p) if tr_p > 0 else 0
    st.metric("BREAKEVEN VOLUME", f"{be_vol:,.0f}")
st.markdown('</div>', unsafe_allow_html=True)
