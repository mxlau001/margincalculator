import streamlit as st
import pandas as pd

# --- STYLING: WHITE/GREY/GREEN THEME ---
st.set_page_config(layout="wide", page_title="Margin Calculator")

st.markdown("""
    <style>
    .stApp { background-color: white; color: #1E824C; font-family: 'Courier New', Courier, monospace; }
    [data-testid="stVerticalBlock"] > div:nth-child(1) { background-color: #f2f2f2; border-radius: 5px; }
    .summary-box {
        border: 2px solid #1E824C;
        padding: 20px;
        border-radius: 10px;
        background-color: white;
    }
    h1, h2, h3, h4, p, span, label { color: #1E824C !important; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- MATH LOGIC ---
def calculate_metrics(df, type="price"):
    df = df.copy()
    # Growth Calculation
    df['Growth %'] = df['Tier Max'].pct_change().fillna(0) * 100
    
    # Discount Calculation: -(D3-D4)/D3
    if type == "price":
        df['Discount %'] = df['Price'].pct_change().fillna(0) * 100
    else:
        df['Discount %'] = df['Rate %'].pct_change().fillna(0) * 100
    return df

def get_margin(val, tiers_upper, rates, mode, is_percentage=False):
    if not val or val == 0: return 0
    tiers = [t for t in tiers_upper if t is not None and t > 0]
    
    # If it's a percentage (Acquiring), convert e.g., 0.60 to 0.006
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

# --- APP LAYOUT ---
st.title("PRICING COMPARISON ENGINE")

col_curr, col_prop = st.columns(2)

def render_section(label):
    with st.container():
        st.subheader(f"{label.upper()} SETUP")
        
        # Inputs with Comma Formatting
        tx = st.number_input(f"Transactions ({label})", value=4200, step=1, format="%d", key=f"tx_{label}")
        vol = st.number_input(f"Volume ({label})", value=4000000000, step=1000, format="%d", key=f"vol_{label}")
        
        # PROCESSING FEES TABLE
        st.markdown("#### PROCESSING FEES")
        proc_data = pd.DataFrame({"Tier Max": [100000, 500000, 1000000], "Price": [10.0, 9.0, 8.0]})
        proc_edited = st.data_editor(
            calculate_metrics(proc_data, "price"), 
            num_rows="dynamic", 
            key=f"p_{label}",
            column_config={
                "Tier Max": st.column_config.NumberColumn("Tier Max", format="%d"),
                "Price": st.column_config.NumberColumn("Price", format="%.2f"),
                "Growth %": st.column_config.NumberColumn("Growth %", format="%.1f%%"),
                "Discount %": st.column_config.NumberColumn("Discount %", format="%.1f%%"),
            }
        )
        
        # ACQUIRING MARKUP TABLE
        st.markdown("#### ACQUIRING MARKUP")
        acq_data = pd.DataFrame({"Tier Max": [300000000, 1000000000, 5000000000], "Rate %": [0.600, 0.492, 0.402]})
        acq_edited = st.data_editor(
            calculate_metrics(acq_data, "rate"), 
            num_rows="dynamic", 
            key=f"a_{label}",
            column_config={
                "Tier Max": st.column_config.NumberColumn("Tier Max", format="%d"),
                "Rate %": st.column_config.NumberColumn("Rate %", format="%.3f%%"),
                "Growth %": st.column_config.NumberColumn("Growth %", format="%.
