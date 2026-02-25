import streamlit as st
import pandas as pd

# --- STYLING: REFINED TRANSPARENT GREY & GREEN ---
st.set_page_config(layout="wide", page_title="Margin Engine")

st.markdown("""
    <style>
    .stApp { background-color: white; color: #1E824C; font-family: 'Courier New', Courier, monospace; }
    
    /* Light Transparent Grey for the Control Panel Area */
    [data-testid="stVerticalBlock"] > div:nth-child(1) { 
        background-color: rgba(242, 242, 242, 0.5); 
        border-radius: 10px; 
        padding: 15px;
    }
    
    /* The Boxed Summary Section */
    .summary-box {
        border: 2px solid #1E824C;
        padding: 25px;
        border-radius: 15px;
        background-color: white;
        margin-top: 20px;
    }
    
    /* Ensure all text/labels remain Green */
    h1, h2, h3, h4, p, span, label, div { color: #1E824C !important; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC: AUTOMATED OUTPUTS ---
def apply_formulas(df, type="price"):
    """Calculates Growth and Discount as non-editable outputs"""
    df = df.copy()
    # Growth: (Current Tier - Prev Tier) / Prev Tier
    df['Growth %'] = df['Tier Max'].pct_change().fillna(0) * 100
    
    # Discount: -(Prev Price - Current Price) / Prev Price
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
        return val * adj_rates[-1]

# --- SIDEBAR ---
with st.sidebar:
    st.header("CONTROLS")
    if st.button("RESET DEFAULTS"):
        st.rerun()

# --- MAIN INTERFACE ---
st.title("PRICING COMPARISON ENGINE")

col_curr, col_prop = st.columns(2)

# Global Column Configuration (Formats numbers with commas and % signs)
table_config = {
    "Tier Max": st.column_config.NumberColumn("Tier Max", format="%d"),
    "Price": st.column_config.NumberColumn("Price", format="%.2f"),
    "Rate %": st.column_config.NumberColumn("Rate %", format="%.3f%%"),
    "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%", help="Automated Output"),
    "Discount %": st.column_config.NumberColumn("Discount %", format="%.1f%%", help="Automated Output")
}

def render_section(label):
    with st.container():
        st.subheader(f"{label.upper()} SETUP")
        
        # Inputs with Thousand Separators (using format="%d")
        tx = st.number_input(f"Transactions ({label})", value=4200, step=1, format="%d", key=f"tx_{label}")
        vol = st.number_input(f"Volume ({label})", value=4000000000, step=1000, format="%d", key=f"vol_{label}")
        
        st.markdown("#### PROCESSING FEES")
        p_data = pd.DataFrame({"Tier Max": [100000, 500000, 1000000], "Price": [10.0, 9.0, 8.0]})
        # We display the calculated metrics but disable editing on those specific columns
        p_edit = st.data_editor(
            apply_formulas(p_data, "price"), 
            num_rows="dynamic", 
            key=f"p_{label}", 
            column_config=table_config,
            disabled=["Growth %", "Discount %"]
        )
        
        st.markdown("#### ACQUIRING MARKUP")
        a_data = pd.DataFrame({"Tier Max": [300000000, 1000000000, 5000000000], "Rate %": [0.600, 0.492, 0.402]})
        a_edit = st.data_editor(
            apply_formulas(a_data, "rate"), 
            num_rows="dynamic", 
            key=f"a_{label}", 
            column_config=table_config,
            disabled=["Growth %", "Discount %"]
        )

        p_m = get_margin(tx, p_edit["Tier Max"].tolist(), p_edit["Price"].tolist(), "Waterfall")
        a_m = get_margin(vol, a_edit["Tier Max"].tolist(), a_edit["Rate %"].tolist(), "Waterfall", is_percentage=True)
        
        return {"total": p_m + a_m, "vol": vol}

with col_curr:
    res_c = render_section("Current")

with col_prop:
    res_p = render_section("Proposal")

# --- FINAL BOXED COMPARISON ---
# The logic here is wrapped in a single <div> to ensure the box contains everything
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
