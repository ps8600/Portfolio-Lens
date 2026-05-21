
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio Lens", layout="wide")

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

st.title("Portfolio Lens")

left, right = st.columns([1, 3])

with left:

    st.header("Inputs")

    eq_bond = st.slider(
        "Equities / Bonds Ratio",
        0.0,
        1.0,
        0.70,
        0.01,
        help="Reference portfolio = 0.70"
    )

    home_bias = st.slider(
        "Home Bias Equities",
        0.0,
        1.0,
        0.60,
        0.01,
        help="Reference portfolio = 0.60"
    )

    yield_curve = st.slider(
        "Yield Curve CHF",
        0.0,
        1.0,
        0.10,
        0.01,
        help="Reference portfolio = 0.10"
    )

    fx_hedge = st.slider(
        "FX Hedging",
        0.0,
        1.0,
        0.00,
        0.01,
        help="Reference portfolio = 0.00"
    )

    user_weights = calculate_user_weights(
        eq_bond,
        home_bias,
        yield_curve,
        fx_hedge
    )

    st.subheader("User Portfolio Weights")

    weights_df = pd.DataFrame({
        "Weight": pd.Series(user_weights)
    })

    st.dataframe(
        (weights_df * 100).round(2),
        use_container_width=True
    )

with right:

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
        title="Portfolio Performance",
        height=650,
        xaxis_title="Date",
        yaxis_title="Index Value",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    metrics = pd.DataFrame({
        "Metric": [
            "Total Return",
            "Volatility"
        ],
        "Reference": [
            f"{(reference_index.iloc[-1] / 100 - 1) * 100:.2f}%",
            f"{df[asset_cols].pct_change().mean(axis=1).std() * np.sqrt(252) * 100:.2f}%"
        ],
        "User": [
            f"{(user_index.iloc[-1] / 100 - 1) * 100:.2f}%",
            f"{df[asset_cols].pct_change().mul(pd.Series(user_weights), axis=1).sum(axis=1).std() * np.sqrt(252) * 100:.2f}%"
        ]
    })

    st.subheader("Performance Metrics")

    st.dataframe(
        metrics,
        use_container_width=True
    )
