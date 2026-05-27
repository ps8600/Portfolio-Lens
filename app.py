import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Portfolio Architecture",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

# Hide Streamlit styling code
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Minimal inline CSS
st.markdown("""
    <style>
    input[type="range"] {
        accent-color: #00FF00;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_path = "20260512_Portfolio Lens_v3.xlsx"

    df = pd.read_excel(file_path, sheet_name="Index")

    asset_cols = [
        "Liquidity",
        "Bonds_CHF",
        "Bonds_IG_HDG",
        "Bonds_IG_UHDG",
        "Equities_CH",
        "Equities_Global_HDG",
        "Equities_Global_UHDG",
        "Real_Estate_CH_listed",
        "Real_Estate_CH_unlisted",
    ]

    df = df[["Date"] + asset_cols]
    df["Date"] = pd.to_datetime(df["Date"])

    return df, asset_cols


def calculate_user_weights(eq_bond, home_bias, yield_curve, fx_hedge):

    start_weights = {
        "Liquidity": 0.03,
        "Bonds_CHF": 0.25,
        "Bonds_IG_HDG": 0.07,
        "Bonds_IG_UHDG": 0.02,
        "Equities_CH": 0.13,
        "Equities_Global_HDG": 0.20,
        "Equities_Global_UHDG": 0.05,
        "Real_Estate_CH_listed": 0.00,
        "Real_Estate_CH_unlisted": 0.25,
    }

    total_portfolio = sum(start_weights.values())

    bond_bucket = (
        start_weights["Liquidity"]
        + start_weights["Bonds_CHF"]
        + start_weights["Bonds_IG_HDG"]
        + start_weights["Bonds_IG_UHDG"]
    )

    equity_bucket = (
        start_weights["Equities_CH"]
        + start_weights["Equities_Global_HDG"]
        + start_weights["Equities_Global_UHDG"]
    )

    c = {}
    c["Liquidity"] = (1 - eq_bond) * total_portfolio * start_weights["Liquidity"] / bond_bucket
    c["Bonds_CHF"] = (1 - eq_bond) * total_portfolio * start_weights["Bonds_CHF"] / bond_bucket
    c["Bonds_IG_HDG"] = (1 - eq_bond) * total_portfolio * start_weights["Bonds_IG_HDG"] / bond_bucket
    c["Bonds_IG_UHDG"] = (1 - eq_bond) * total_portfolio * start_weights["Bonds_IG_UHDG"] / bond_bucket

    d = {}
    d["Liquidity"] = c["Liquidity"]
    d["Bonds_CHF"] = yield_curve * (
        c["Bonds_CHF"] + c["Bonds_IG_HDG"] + c["Bonds_IG_UHDG"]
    )

    remaining_bonds = (
        c["Bonds_IG_HDG"] + c["Bonds_IG_UHDG"]
    )

    if remaining_bonds > 0:
        d["Bonds_IG_HDG"] = (
            (1 - yield_curve)
            * (c["Bonds_CHF"] + c["Bonds_IG_HDG"] + c["Bonds_IG_UHDG"])
            * c["Bonds_IG_HDG"]
            / remaining_bonds
        )

        d["Bonds_IG_UHDG"] = (
            (1 - yield_curve)
            * (c["Bonds_CHF"] + c["Bonds_IG_HDG"] + c["Bonds_IG_UHDG"])
            * c["Bonds_IG_UHDG"]
            / remaining_bonds
        )
    else:
        d["Bonds_IG_HDG"] = 0
        d["Bonds_IG_UHDG"] = 0

    c["Equities_CH"] = eq_bond * total_portfolio * start_weights["Equities_CH"] / equity_bucket
    c["Equities_Global_HDG"] = eq_bond * total_portfolio * start_weights["Equities_Global_HDG"] / equity_bucket
    c["Equities_Global_UHDG"] = eq_bond * total_portfolio * start_weights["Equities_Global_UHDG"] / equity_bucket

    d["Equities_CH"] = home_bias * (
        c["Equities_CH"] + c["Equities_Global_HDG"] + c["Equities_Global_UHDG"]
    )

    remaining_equities = (
        c["Equities_Global_HDG"] + c["Equities_Global_UHDG"]
    )

    if remaining_equities > 0:
        d["Equities_Global_HDG"] = (
            (1 - home_bias)
            * (c["Equities_CH"] + c["Equities_Global_HDG"] + c["Equities_Global_UHDG"])
            * c["Equities_Global_HDG"]
            / remaining_equities
        )

        d["Equities_Global_UHDG"] = (
            (1 - home_bias)
            * (c["Equities_CH"] + c["Equities_Global_HDG"] + c["Equities_Global_UHDG"])
            * c["Equities_Global_UHDG"]
            / remaining_equities
        )
    else:
        d["Equities_Global_HDG"] = 0
        d["Equities_Global_UHDG"] = 0

    d["Real_Estate_CH_listed"] = 0
    d["Real_Estate_CH_unlisted"] = 0.25

    e = {}
    e["Liquidity"] = d["Liquidity"]
    e["Bonds_CHF"] = d["Bonds_CHF"]

    e["Bonds_IG_HDG"] = fx_hedge * (
        d["Bonds_IG_HDG"] + d["Bonds_IG_UHDG"]
    )

    e["Bonds_IG_UHDG"] = (1 - fx_hedge) * (
        d["Bonds_IG_HDG"] + d["Bonds_IG_UHDG"]
    )

    e["Equities_CH"] = d["Equities_CH"]

    e["Equities_Global_HDG"] = fx_hedge * (
        d["Equities_Global_HDG"] + d["Equities_Global_UHDG"]
    )

    e["Equities_Global_UHDG"] = (1 - fx_hedge) * (
        d["Equities_Global_HDG"] + d["Equities_Global_UHDG"]
    )

    e["Real_Estate_CH_listed"] = d["Real_Estate_CH_listed"]
    e["Real_Estate_CH_unlisted"] = d["Real_Estate_CH_unlisted"]

    return e


def calculate_portfolio_returns(df, weights, asset_cols):
    """Calculate cumulative returns starting from 0%"""
    returns = df[asset_cols].pct_change().fillna(0)
    
    weighted_returns = returns.mul(
        pd.Series(weights),
        axis=1
    ).sum(axis=1)
    
    # Calculate cumulative returns (starting from 0%)
    cumulative_returns = (1 + weighted_returns).cumprod() - 1
    
    return cumulative_returns * 100  # Convert to percentage


df, asset_cols = load_data()

reference_weights = {
    "Liquidity": 0.03,
    "Bonds_CHF": 0.25,
    "Bonds_IG_HDG": 0.07,
    "Bonds_IG_UHDG": 0.02,
    "Equities_CH": 0.13,
    "Equities_Global_HDG": 0.20,
    "Equities_Global_UHDG": 0.05,
    "Real_Estate_CH_listed": 0.00,
    "Real_Estate_CH_unlisted": 0.25,
}

# Initialize session state for active input and slider values
if "eq_bond_value" not in st.session_state:
    st.session_state.eq_bond_value = 0.50

if "home_bias_value" not in st.session_state:
    st.session_state.home_bias_value = 1/3

if "yield_curve_value" not in st.session_state:
    st.session_state.yield_curve_value = 0.75

if "fx_hedge_value" not in st.session_state:
    st.session_state.fx_hedge_value = 0.80

# Main title
st.title("Portfolio Architecture")

# Strategic Exposure section
st.markdown("## Strategic Exposure")

# Compact slider layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Equities/Bonds Ratio**")
    col_min, col_slider, col_val, col_max = st.columns([0.1, 4, 0.3, 0.1])
    with col_min:
        st.write("0%")
    with col_slider:
        st.session_state.eq_bond_value = st.slider(
            "Equities/Bonds Ratio",
            0.0,
            1.0,
            st.session_state.eq_bond_value,
            0.01,
            label_visibility="collapsed",
            format="%.0f%%"
        )
    with col_val:
        st.markdown(f"<div style='text-align: right; color: #00FF00; font-weight: bold;'>{st.session_state.eq_bond_value*100:.0f}%</div>", unsafe_allow_html=True)
    with col_max:
        st.write("100%")
    st.caption("½ = 50%")
    
    st.markdown("**Yield Curve CHF**")
    col_min, col_slider, col_val, col_max = st.columns([0.1, 4, 0.3, 0.1])
    with col_min:
        st.write("0%")
    with col_slider:
        st.session_state.yield_curve_value = st.slider(
            "Yield Curve CHF",
            0.0,
            1.0,
            st.session_state.yield_curve_value,
            0.01,
            label_visibility="collapsed",
            format="%.0f%%"
        )
    with col_val:
        st.markdown(f"<div style='text-align: right; color: #00FF00; font-weight: bold;'>{st.session_state.yield_curve_value*100:.0f}%</div>", unsafe_allow_html=True)
    with col_max:
        st.write("100%")
    st.caption("¾ = 75%")

with col2:
    st.markdown("**Home Bias Equities**")
    col_min, col_slider, col_val, col_max = st.columns([0.1, 4, 0.3, 0.1])
    with col_min:
        st.write("0%")
    with col_slider:
        st.session_state.home_bias_value = st.slider(
            "Home Bias Equities",
            0.0,
            1.0,
            st.session_state.home_bias_value,
            0.01,
            label_visibility="collapsed",
            format="%.0f%%"
        )
    with col_val:
        st.markdown(f"<div style='text-align: right; color: #00FF00; font-weight: bold;'>{st.session_state.home_bias_value*100:.0f}%</div>", unsafe_allow_html=True)
    with col_max:
        st.write("100%")
    st.caption("⅓ = 33%")
    
    st.markdown("**FX Hedging**")
    col_min, col_slider, col_val, col_max = st.columns([0.1, 4, 0.3, 0.1])
    with col_min:
        st.write("0%")
    with col_slider:
        st.session_state.fx_hedge_value = st.slider(
            "FX Hedging",
            0.0,
            1.0,
            st.session_state.fx_hedge_value,
            0.01,
            label_visibility="collapsed",
            format="%.0f%%"
        )
    with col_val:
        st.markdown(f"<div style='text-align: right; color: #00FF00; font-weight: bold;'>{st.session_state.fx_hedge_value*100:.0f}%</div>", unsafe_allow_html=True)
    with col_max:
        st.write("100%")
    st.caption("⅘ = 80%")

# Reset to reference button
col_button1, col_button2, col_button3 = st.columns([1, 4, 1])
with col_button1:
    if st.button("📍 Reset", use_container_width=True):
        st.session_state.eq_bond_value = 0.50
        st.session_state.home_bias_value = 1/3
        st.session_state.yield_curve_value = 0.75
        st.session_state.fx_hedge_value = 0.80
        st.rerun()

user_weights = calculate_user_weights(
    st.session_state.eq_bond_value,
    st.session_state.home_bias_value,
    st.session_state.yield_curve_value,
    st.session_state.fx_hedge_value
)

# Performance section
st.markdown("## Performance")

reference_returns = calculate_portfolio_returns(
    df,
    reference_weights,
    asset_cols
)

user_returns = calculate_portfolio_returns(
    df,
    user_weights,
    asset_cols
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=reference_returns,
        mode="lines",
        name="Reference",
        line=dict(color="#808080", width=2, dash="dash"),
        hovertemplate="<b>Reference</b><br>Date: %{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra></extra>"
    )
)

fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=user_returns,
        mode="lines",
        name="User",
        line=dict(color="#00FF00", width=3),
        hovertemplate="<b>User</b><br>Date: %{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra></extra>"
    )
)

# Add a horizontal line at y=0%
fig.add_hline(
    y=0,
    line_dash="solid",
    line_color="rgba(100,100,100,0.3)",
    line_width=1
)

fig.update_layout(
    height=450,
    xaxis_title=None,
    yaxis_title=None,
    hovermode="x unified",
    showlegend=False,
    margin=dict(l=50, r=20, t=20, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(size=12, family="Segoe UI, -apple-system, BlinkMacSystemFont, Roboto"),
    xaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False
    ),
    yaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False,
        ticksuffix="%"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False, "responsive": True}
)
