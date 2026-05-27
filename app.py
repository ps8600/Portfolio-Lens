
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Swiss Pension Funds - Portfolio Analysis", layout="wide")

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

st.title("Swiss Pension Funds - Portfolio Analysis")

# Define input descriptions
input_descriptions = {
    "Equities/Bonds Ratio": "Swiss pension funds allocate approximately 25% of their investments to real estate, with the remaining 75% split equally between equities and bonds. The Equities/Bonds Ratio indicates the percentage of equities in the liquid portfolio (excluding real estate). For example, a ratio of 100% means all investments are in equities with no bonds, while 25% real estate is included in the overall allocation.",
    "Home Bias Equities": "Swiss pension funds allocate approximately 1/3 of their listed equities to Swiss stocks. A ratio of 100% indicates that all listed equities are Swiss stocks.",
    "Yield Curve CHF": "Swiss pension funds invest approximately 3/4 of their bonds in CHF-denominated securities. A ratio of 100% indicates that all bonds are issued in Swiss francs.",
    "FX Hedging": "Swiss pension funds hedge approximately 80% of their foreign currency exposure. A ratio of 100% indicates that all foreign currency risk is fully hedged."
}

left, right = st.columns([1, 3])

with left:
    # User Input header with horizontal icons
    header_col1, header_col2 = st.columns([1, 1.5])
    
    with header_col1:
        st.markdown("#### **Portfolio Cockpit**")
    
    with header_col2:
        icon_cols = st.columns(4, gap="small")
        
        with icon_cols[0]:
            if st.button("⚖️", key="eq_bond_btn", help="Equities/Bonds Ratio"):
                st.session_state.active_input = "Equities/Bonds Ratio"
                st.rerun()
            # Highlight if active
            if st.session_state.active_input == "Equities/Bonds Ratio":
                st.markdown(
                    '<div style="position: relative; top: -50px; left: 0px; width: 40px; height: 40px; background-color: #0052CC; border-radius: 8px; z-index: -1;"></div>',
                    unsafe_allow_html=True
                )
        
        with icon_cols[1]:
            if st.button("🏠", key="home_bias_btn", help="Home Bias Equities"):
                st.session_state.active_input = "Home Bias Equities"
                st.rerun()
            if st.session_state.active_input == "Home Bias Equities":
                st.markdown(
                    '<div style="position: relative; top: -50px; left: 0px; width: 40px; height: 40px; background-color: #0052CC; border-radius: 8px; z-index: -1;"></div>',
                    unsafe_allow_html=True
                )
        
        with icon_cols[2]:
            if st.button("📈", key="yield_btn", help="Yield Curve CHF"):
                st.session_state.active_input = "Yield Curve CHF"
                st.rerun()
            if st.session_state.active_input == "Yield Curve CHF":
                st.markdown(
                    '<div style="position: relative; top: -50px; left: 0px; width: 40px; height: 40px; background-color: #0052CC; border-radius: 8px; z-index: -1;"></div>',
                    unsafe_allow_html=True
                )
        
        with icon_cols[3]:
            if st.button("🛡️", key="fx_btn", help="FX Hedging"):
                st.session_state.active_input = "FX Hedging"
                st.rerun()
            if st.session_state.active_input == "FX Hedging":
                st.markdown(
                    '<div style="position: relative; top: -50px; left: 0px; width: 40px; height: 40px; background-color: #0052CC; border-radius: 8px; z-index: -1;"></div>',
                    unsafe_allow_html=True
                )
    
    st.divider()
    
    # Display active input slider
    if st.session_state.active_input == "Equities/Bonds Ratio":
        st.session_state.eq_bond_value = st.slider(
            "Equities / Bonds Ratio",
            0.0,
            1.0,
            st.session_state.eq_bond_value,
            0.01,
            help=input_descriptions["Equities/Bonds Ratio"],
            label_visibility="visible"
        )
        
    elif st.session_state.active_input == "Home Bias Equities":
        st.session_state.home_bias_value = st.slider(
            "Home Bias Equities",
            0.0,
            1.0,
            st.session_state.home_bias_value,
            0.01,
            help=input_descriptions["Home Bias Equities"],
            label_visibility="visible"
        )
        
    elif st.session_state.active_input == "Yield Curve CHF":
        st.session_state.yield_curve_value = st.slider(
            "Yield Curve CHF",
            0.0,
            1.0,
            st.session_state.yield_curve_value,
            0.01,
            help=input_descriptions["Yield Curve CHF"],
            label_visibility="visible"
        )
        
    else:  # FX Hedging
        st.session_state.fx_hedge_value = st.slider(
            "FX Hedging",
            0.0,
            1.0,
            st.session_state.fx_hedge_value,
            0.01,
            help=input_descriptions["FX Hedging"],
            label_visibility="visible"
        )

    user_weights = calculate_user_weights(
        st.session_state.eq_bond_value,
        st.session_state.home_bias_value,
        st.session_state.yield_curve_value,
        st.session_state.fx_hedge_value
    )

with right:
    st.markdown("#### **Portfolio Performance**")
    st.divider()

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
            name="Reference Portfolio"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=user_index,
            mode="lines",
            name="User Portfolio"
        )
    )

    fig.update_layout(
        height=650,
        xaxis_title="Date",
        yaxis_title="Index Value",
        hovermode="x unified",
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
