
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Swiss Pension Funds - Portfolio Analysis",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

# Custom CSS for responsive design and Edge compatibility
st.markdown("""
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    /* Reset and base styles for Edge compatibility */
    * {
        box-sizing: border-box;
    }
    
    html, body {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Main title styling */
    h1 {
        font-size: 2rem;
        margin-bottom: 2rem;
        font-weight: 600;
        color: #262730;
    }
    
    /* Section headers */
    h2 {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #262730;
    }
    
    /* Cockpit container */
    .cockpit-container {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Icon buttons styling */
    .icon-button {
        display: inline-block;
        width: 44px;
        height: 44px;
        padding: 0;
        margin: 0 4px;
        border-radius: 8px;
        border: 1px solid transparent;
        background-color: #e8eef2;
        cursor: pointer;
        font-size: 1.2rem;
        transition: background-color 0.2s ease, border-color 0.2s ease;
        text-align: center;
        line-height: 44px;
    }
    
    .icon-button.active {
        background-color: #0052CC;
        color: white;
        border-color: #0052CC;
    }
    
    .icon-button:hover {
        background-color: #d0d8e0;
        border-color: #d0d8e0;
    }
    
    .icon-button.active:hover {
        background-color: #0052CC;
        border-color: #0052CC;
    }
    
    /* Slider styling */
    .slider-container {
        background-color: #e8f0f8;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid #d0e4f7;
    }
    
    /* Performance chart container */
    .performance-container {
        background-color: #faf8f3;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #f0ede6;
    }
    
    /* Input and button styles */
    input[type="range"],
    input[type="text"],
    input[type="number"],
    select {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.95rem;
    }
    
    button {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Ensure proper text rendering in Edge */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }
    
    @media (max-width: 900px) {
        h1 {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        h2 {
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }
        
        .cockpit-container {
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .slider-container {
            padding: 1rem;
            margin-top: 0.8rem;
        }
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


def calculate_portfolio_index(df, weights, asset_cols):

    returns = df[asset_cols].pct_change().fillna(0)

    weighted_returns = returns.mul(
        pd.Series(weights),
        axis=1
    ).sum(axis=1)

    index_series = 100 * (1 + weighted_returns).cumprod()

    return index_series


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
if "active_input" not in st.session_state:
    st.session_state.active_input = "Equities/Bonds Ratio"

if "eq_bond_value" not in st.session_state:
    st.session_state.eq_bond_value = 0.50

if "home_bias_value" not in st.session_state:
    st.session_state.home_bias_value = 0.33

if "yield_curve_value" not in st.session_state:
    st.session_state.yield_curve_value = 0.75

if "fx_hedge_value" not in st.session_state:
    st.session_state.fx_hedge_value = 0.80

# Main title
st.title("Swiss Pension Funds - Portfolio Analysis")

# Define input descriptions
input_descriptions = {
    "Equities/Bonds Ratio": "Swiss pension funds allocate approximately 25% of their investments to real estate, with the remaining 75% split equally between equities and bonds. The Equities/Bond ratio determines this allocation.",
    "Home Bias Equities": "Swiss pension funds allocate approximately 1/3 of their listed equities to Swiss stocks. A ratio of 100% indicates that all listed equities are Swiss stocks.",
    "Yield Curve CHF": "Swiss pension funds invest approximately 3/4 of their bonds in CHF-denominated securities. A ratio of 100% indicates that all bonds are issued in Swiss francs.",
    "FX Hedging": "Swiss pension funds hedge approximately 80% of their foreign currency exposure. A ratio of 100% indicates that all foreign currency risk is fully hedged."
}

# Portfolio Cockpit section
st.markdown("## Portfolio Cockpit")

# Icon selector row
col_icons = st.columns([0.3, 0.7], gap="small")
with col_icons[1]:
    icon_cols = st.columns(4, gap="small")
    
    icons = [
        ("⚖️", "Equities/Bonds Ratio"),
        ("🏠", "Home Bias Equities"),
        ("📈", "Yield Curve CHF"),
        ("🛡️", "FX Hedging")
    ]
    
    for i, (icon, label) in enumerate(icons):
        with icon_cols[i]:
            is_active = st.session_state.active_input == label
            button_style = "active" if is_active else ""
            if st.button(icon, key=f"icon_{i}", help=label, use_container_width=True):
                st.session_state.active_input = label
                st.rerun()

# Slider container
with st.container():
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    
    if st.session_state.active_input == "Equities/Bonds Ratio":
        label = "Equities/Bonds Ratio"
        col1, col2, col3 = st.columns([1.5, 3, 0.5])
        with col1:
            st.write(label)
        with col2:
            st.session_state.eq_bond_value = st.slider(
                label,
                0.0,
                1.0,
                st.session_state.eq_bond_value,
                0.01,
                help=input_descriptions[label],
                label_visibility="collapsed"
            )
        with col3:
            st.write(f"{st.session_state.eq_bond_value*100:.0f}%")
        
    elif st.session_state.active_input == "Home Bias Equities":
        label = "Home Bias Equities"
        col1, col2, col3 = st.columns([1.5, 3, 0.5])
        with col1:
            st.write(label)
        with col2:
            st.session_state.home_bias_value = st.slider(
                label,
                0.0,
                1.0,
                st.session_state.home_bias_value,
                0.01,
                help=input_descriptions[label],
                label_visibility="collapsed"
            )
        with col3:
            st.write(f"{st.session_state.home_bias_value*100:.0f}%")
        
    elif st.session_state.active_input == "Yield Curve CHF":
        label = "Yield Curve CHF"
        col1, col2, col3 = st.columns([1.5, 3, 0.5])
        with col1:
            st.write(label)
        with col2:
            st.session_state.yield_curve_value = st.slider(
                label,
                0.0,
                1.0,
                st.session_state.yield_curve_value,
                0.01,
                help=input_descriptions[label],
                label_visibility="collapsed"
            )
        with col3:
            st.write(f"{st.session_state.yield_curve_value*100:.0f}%")
        
    else:  # FX Hedging
        label = "FX Hedging"
        col1, col2, col3 = st.columns([1.5, 3, 0.5])
        with col1:
            st.write(label)
        with col2:
            st.session_state.fx_hedge_value = st.slider(
                label,
                0.0,
                1.0,
                st.session_state.fx_hedge_value,
                0.01,
                help=input_descriptions[label],
                label_visibility="collapsed"
            )
        with col3:
            st.write(f"{st.session_state.fx_hedge_value*100:.0f}%")
    
    st.markdown('</div>', unsafe_allow_html=True)

user_weights = calculate_user_weights(
    st.session_state.eq_bond_value,
    st.session_state.home_bias_value,
    st.session_state.yield_curve_value,
    st.session_state.fx_hedge_value
)

# Performance section
st.markdown("## Performance")

with st.container():
    st.markdown('<div class="performance-container">', unsafe_allow_html=True)
    
    reference_index = calculate_portfolio_index(
        df,
        reference_weights,
        asset_cols
    )

    user_index = calculate_portfolio_index(
        df,
        user_weights,
        asset_cols
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=reference_index,
            mode="lines",
            name="Reference Portfolio",
            line=dict(color="#e0e0e0", width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=user_index,
            mode="lines",
            name="User Portfolio",
            line=dict(color="#0052CC", width=2)
        )
    )

    fig.update_layout(
        height=450,
        xaxis_title=None,
        yaxis_title=None,
        hovermode="x unified",
        showlegend=True,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="#faf8f3",
        plot_bgcolor="#faf8f3",
        font=dict(size=12, family="Segoe UI, -apple-system, BlinkMacSystemFont, Roboto"),
        legend=dict(
            x=0.5,
            y=-0.15,
            xanchor="center",
            yanchor="top",
            orientation="h"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True}
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
