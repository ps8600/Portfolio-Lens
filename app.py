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

# Custom CSS for responsive design and finance-appropriate styling
st.markdown("""
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    /* Reset and base styles */
    * {
        box-sizing: border-box;
    }
    
    html, body {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Color scheme - professional finance with neon green accents */
    :root {
        --primary-neon: #00FF00;
        --primary-neon-dark: #00CC00;
        --dark-bg: #0a0e27;
        --dark-surface: #1a1f3a;
        --light-bg: #ffffff;
        --light-surface: #f5f7fa;
        --text-dark: #1a1a1a;
        --text-light: #e8e8e8;
        --accent-positive: #00FF00;
        --accent-neutral: #4a5568;
    }
    
    /* Light mode */
    [data-theme="light"] {
        --bg-primary: var(--light-bg);
        --bg-secondary: var(--light-surface);
        --text-primary: var(--text-dark);
        --border-color: #e0e0e0;
        --accent-color: #00CC00;
    }
    
    /* Dark mode */
    [data-theme="dark"] {
        --bg-primary: var(--dark-bg);
        --bg-secondary: var(--dark-surface);
        --text-primary: var(--text-light);
        --border-color: #2a2a3e;
        --accent-color: var(--primary-neon);
    }
    
    /* Main title styling */
    h1 {
        font-size: 2rem;
        margin-bottom: 1.5rem;
        font-weight: 700;
        color: var(--accent-color);
        letter-spacing: -0.5px;
    }
    
    /* Section headers */
    h2 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    
    /* Dropdown container */
    .dropdown-container {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    
    /* Slider container */
    .slider-container {
        background-color: var(--bg-secondary);
        padding: 0.75rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        border: 1px solid var(--border-color);
    }
    
    /* Performance chart container - transparent background */
    .performance-container {
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* Slider styling override */
    input[type="range"] {
        accent-color: var(--accent-color);
    }
    
    /* Input and button styles */
    input[type="range"],
    input[type="text"],
    input[type="number"],
    select {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.95rem;
        color: var(--text-primary);
        background-color: var(--bg-primary);
        border-color: var(--border-color);
    }
    
    button {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border-color: var(--border-color);
    }
    
    /* Text styling */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        color: var(--text-primary);
        background-color: var(--bg-primary);
    }
    
    /* Responsive design */
    @media (max-width: 1024px) {
        h1 {
            font-size: 1.7rem;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .dropdown-container,
        .slider-container,
        .performance-container {
            padding: 0.75rem;
            margin-bottom: 0.75rem;
        }
    }
    
    @media (max-width: 768px) {
        h1 {
            font-size: 1.4rem;
        }
        
        h2 {
            font-size: 1rem;
        }
        
        .dropdown-container,
        .slider-container,
        .performance-container {
            padding: 0.5rem;
        }
    }
    
    /* Label styling */
    .input-label {
        font-weight: 600;
        margin-bottom: 0.25rem;
        display: block;
        color: var(--text-primary);
        font-size: 0.95rem;
    }
    
    .value-display {
        text-align: right;
        font-weight: 600;
        color: var(--accent-color);
        min-width: 50px;
        font-size: 0.9rem;
    }
    
    .info-text {
        font-size: 0.8rem;
        color: var(--accent-neutral);
        margin-top: 0.25rem;
        line-height: 1.3;
    }
    
    .reference-indicator {
        font-size: 0.75rem;
        color: #888888;
        margin-top: 0.1rem;
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
    st.session_state.home_bias_value = 0.33

if "yield_curve_value" not in st.session_state:
    st.session_state.yield_curve_value = 0.75

if "fx_hedge_value" not in st.session_state:
    st.session_state.fx_hedge_value = 0.80

# Main title
st.title("Portfolio Architecture")

# Define input descriptions and reference values
input_config = {
    "Equities/Bonds Ratio": {
        "description": "Allocate between equities and bonds. Swiss pension funds typically allocate 50% to equities and 50% to bonds (excluding real estate).",
        "reference": 0.50,
        "reference_display": "50%"
    },
    "Home Bias Equities": {
        "description": "Allocate between Swiss and global equities. Swiss pension funds typically allocate 1/3 to Swiss stocks and 2/3 to global stocks.",
        "reference": 1/3,
        "reference_display": "33%"
    },
    "Yield Curve CHF": {
        "description": "Allocate between CHF-denominated and foreign bonds. Swiss pension funds typically allocate 75% to CHF bonds and 25% to foreign bonds.",
        "reference": 0.75,
        "reference_display": "75%"
    },
    "FX Hedging": {
        "description": "Control FX hedging of foreign currency exposure. Swiss pension funds typically hedge approximately 80% of their foreign currency exposure.",
        "reference": 0.80,
        "reference_display": "80%"
    }
}

# Strategic Exposure section
st.markdown("## Strategic Exposure")

with st.container():
    st.markdown('<div class="dropdown-container">', unsafe_allow_html=True)
    
    # Use expanders for responsive design
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("⚖️ Equities/Bonds Ratio", expanded=True):
            st.markdown('<span class="input-label">Equities/Bonds Ratio</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text">{input_config["Equities/Bonds Ratio"]["description"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reference-indicator">Reference: {input_config["Equities/Bonds Ratio"]["reference_display"]}</div>', unsafe_allow_html=True)
            
            st.session_state.eq_bond_value = st.slider(
                "Equities/Bonds Ratio",
                0.0,
                1.0,
                st.session_state.eq_bond_value,
                0.01,
                label_visibility="collapsed"
            )
            col_val, col_pct = st.columns([1, 0.5])
            with col_pct:
                st.markdown(f'<div class="value-display">{st.session_state.eq_bond_value*100:.0f}%</div>', unsafe_allow_html=True)
        
        with st.expander("📈 Yield Curve CHF"):
            st.markdown('<span class="input-label">Yield Curve CHF</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text">{input_config["Yield Curve CHF"]["description"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reference-indicator">Reference: {input_config["Yield Curve CHF"]["reference_display"]}</div>', unsafe_allow_html=True)
            
            st.session_state.yield_curve_value = st.slider(
                "Yield Curve CHF",
                0.0,
                1.0,
                st.session_state.yield_curve_value,
                0.01,
                label_visibility="collapsed"
            )
            col_val, col_pct = st.columns([1, 0.5])
            with col_pct:
                st.markdown(f'<div class="value-display">{st.session_state.yield_curve_value*100:.0f}%</div>', unsafe_allow_html=True)
    
    with col2:
        with st.expander("🏠 Home Bias Equities"):
            st.markdown('<span class="input-label">Home Bias Equities</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text">{input_config["Home Bias Equities"]["description"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reference-indicator">Reference: {input_config["Home Bias Equities"]["reference_display"]}</div>', unsafe_allow_html=True)
            
            st.session_state.home_bias_value = st.slider(
                "Home Bias Equities",
                0.0,
                1.0,
                st.session_state.home_bias_value,
                0.01,
                label_visibility="collapsed"
            )
            col_val, col_pct = st.columns([1, 0.5])
            with col_pct:
                st.markdown(f'<div class="value-display">{st.session_state.home_bias_value*100:.0f}%</div>', unsafe_allow_html=True)
        
        with st.expander("🛡️ FX Hedging"):
            st.markdown('<span class="input-label">FX Hedging</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-text">{input_config["FX Hedging"]["description"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reference-indicator">Reference: {input_config["FX Hedging"]["reference_display"]}</div>', unsafe_allow_html=True)
            
            st.session_state.fx_hedge_value = st.slider(
                "FX Hedging",
                0.0,
                1.0,
                st.session_state.fx_hedge_value,
                0.01,
                label_visibility="collapsed"
            )
            col_val, col_pct = st.columns([1, 0.5])
            with col_pct:
                st.markdown(f'<div class="value-display">{st.session_state.fx_hedge_value*100:.0f}%</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Reset to reference button
col_button1, col_button2, col_button3 = st.columns([1, 4, 1])
with col_button1:
    if st.button("📍 Reset to Reference", use_container_width=True):
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

with st.container():
    st.markdown('<div class="performance-container">', unsafe_allow_html=True)
    
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
            name="Reference Portfolio",
            line=dict(color="#808080", width=2, dash="dash")
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=user_returns,
            mode="lines",
            name="User Portfolio",
            line=dict(color="#00FF00", width=3)
        )
    )

    # Add a horizontal line at y=0%
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="rgba(100,100,100,0.3)",
        line_width=1,
        annotation_text="",
        annotation_position="right"
    )

    fig.update_layout(
        height=400,
        xaxis_title=None,
        yaxis_title="Cumulative Return (%)",
        hovermode="x unified",
        showlegend=True,
        margin=dict(l=50, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, family="Segoe UI, -apple-system, BlinkMacSystemFont, Roboto", color="rgba(0,0,0,0.8)"),
        legend=dict(
            x=0.0,
            y=1.0,
            xanchor="left",
            yanchor="top",
            orientation="h",
            bgcolor="rgba(255,255,255,0)",
            bordercolor="rgba(0,0,0,0)",
            borderwidth=0
        ),
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
            zeroline=False
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True}
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
