"""
app.py  —  QuantView: US Stock Quantitative Analytics
Run with:  streamlit run app.py
"""

import sys
import os
import pandas as pd
from datetime import date, timedelta

import streamlit as st

# Make sure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_fetcher import (
    fetch_stock_data,
    fetch_ticker_info,
    fetch_benchmark_data,
    get_close_prices,
    fetch_stock_data as _fetch,
)
from metrics import (
    compute_all_metrics,
    compute_daily_returns,
    compute_rsi,
    compute_bollinger_bands,
    compute_moving_averages,
    compute_drawdown_series,
)
from charts import (
    plot_price_chart,
    plot_candlestick,
    plot_rsi_chart,
    plot_bollinger_chart,
    plot_drawdown,
    plot_returns_distribution,
    plot_comparison_chart,
    plot_rolling_sharpe,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantView | US Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* App background */
.stApp { background-color: #0A0E1A; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1322 0%, #0A0E1A 100%);
    border-right: 1px solid #1E2740;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #1C2236;
    border: 1px solid #252D42;
    border-radius: 14px;
    padding: 18px 20px;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #6366F1; }

/* Tab bar */
.stTabs [data-baseweb="tab-list"] {
    background: #131829;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1E2740;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #64748B;
    font-weight: 500;
    padding: 8px 20px;
    transition: color 0.15s;
}
.stTabs [aria-selected="true"] {
    background: #6366F1 !important;
    color: #fff !important;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    border: none;
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: opacity 0.2s, transform 0.15s;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* Input fields */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: #1C2236 !important;
    border: 1px solid #252D42 !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] { background: #252D42; }

/* Dividers */
hr { border-color: #1E2740 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0A0E1A; }
::-webkit-scrollbar-thumb { background: #252D42; border-radius: 4px; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Section headers */
.section-title {
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 16px 0 8px 0;
}

/* Hero card */
.hero-card {
    background: linear-gradient(135deg, #131829 0%, #1C2236 100%);
    border: 1px solid #252D42;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
}

/* Feature card */
.feature-card {
    background: #131829;
    border: 1px solid #1E2740;
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s;
    height: 100%;
}
.feature-card:hover {
    border-color: #6366F1;
    transform: translateY(-2px);
}

/* Comparison table */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Badge pill */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
}
.badge-up   { background: rgba(16,185,129,0.15); color: #10B981; }
.badge-down { background: rgba(239,68,68,0.15);  color: #EF4444; }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Session state helpers ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "analyzed": False,
        "data": None,
        "benchmark": None,
        "info": {},
        "ticker": "",
        "start": date.today() - timedelta(days=365),
        "end": date.today(),
        "rf": 0.045,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 8px 0 16px 0;">
            <span style="font-size:28px;">📈</span>
            <span style="font-size:22px; font-weight:700; color:#E2E8F0; margin-left:8px;">QuantView</span>
            <div style="font-size:12px; color:#64748B; margin-top:4px;">US Stock Quantitative Analytics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div class="section-title">📌 Ticker</div>', unsafe_allow_html=True)
    ticker_input = st.text_input(
        "Stock Symbol",
        value="AAPL",
        placeholder="e.g. AAPL, TSLA, SPY",
        label_visibility="collapsed",
    ).upper().strip()

    st.markdown('<div class="section-title">📅 Time Range</div>', unsafe_allow_html=True)
    preset = st.radio(
        "Range",
        options=["1M", "3M", "6M", "1Y", "2Y", "5Y", "Custom"],
        index=3,
        horizontal=False,
        label_visibility="collapsed",
    )

    if preset == "Custom":
        col_a, col_b = st.columns(2)
        with col_a:
            start_input = st.date_input("Start", value=date.today() - timedelta(days=365))
        with col_b:
            end_input = st.date_input("End", value=date.today())
    else:
        end_input = date.today()
        days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730, "5Y": 1825}
        start_input = end_input - timedelta(days=days_map[preset])

    st.markdown('<div class="section-title">📊 Risk-Free Rate</div>', unsafe_allow_html=True)
    rf_input = st.slider(
        "Risk-Free Rate (%)",
        min_value=0.0, max_value=10.0, value=4.5, step=0.1,
        format="%.1f%%",
        label_visibility="collapsed",
        help="Used for Sharpe, Sortino, Alpha calculations. Default ≈ US 10Y Treasury.",
    ) / 100

    st.divider()

    analyze_clicked = st.button(
        "🔍  Analyze",
        use_container_width=True,
        type="primary",
    )

    st.markdown(
        """
        <div style="font-size:11px; color:#374151; margin-top:16px; line-height:1.6;">
        ⚠️ For educational purposes only.<br>Not investment advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Data fetch on button click ───────────────────────────────────────────────
if analyze_clicked and ticker_input:
    with st.spinner(f"Fetching {ticker_input} data…"):
        raw_data = fetch_stock_data(ticker_input, str(start_input), str(end_input))

    if raw_data is None or raw_data.empty:
        st.error(f"❌ No data found for **'{ticker_input}'**. Please verify the ticker symbol.")
        st.stop()

    with st.spinner("Fetching benchmark (SPY)…"):
        bm_data = fetch_benchmark_data(str(start_input), str(end_input))

    with st.spinner("Loading company info…"):
        info = fetch_ticker_info(ticker_input)

    # Persist to session state
    st.session_state.update(
        analyzed=True,
        data=raw_data,
        benchmark=bm_data,
        info=info,
        ticker=ticker_input,
        start=start_input,
        end=end_input,
        rf=rf_input,
    )


# ─── Landing page ─────────────────────────────────────────────────────────────
if not st.session_state.analyzed:
    st.markdown(
        """
        <div style="text-align:center; padding: 72px 0 32px;">
            <div style="font-size:64px;">📈</div>
            <h1 style="font-size:40px; font-weight:700; color:#E2E8F0; margin:16px 0 8px;">QuantView</h1>
            <p style="font-size:18px; color:#64748B; margin-bottom:4px;">
                US Stock Quantitative Analytics Platform
            </p>
            <p style="color:#374151; font-size:15px;">
                Enter a ticker on the left and click <b>Analyze</b> to begin.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("📊", "Sharpe Ratio", "Risk-adjusted returns with configurable risk-free rate"),
        ("📉", "Max Drawdown", "Peak-to-trough loss, drawdown time series"),
        ("⚙️", "RSI & Bollinger", "Technical indicators with interactive charts"),
        ("⚖️", "Comparison", "Normalize & compare up to 3 tickers side-by-side"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div style="font-size:32px; margin-bottom:12px;">{icon}</div>
                    <div style="font-size:15px; font-weight:600; color:#E2E8F0; margin-bottom:8px;">{title}</div>
                    <div style="font-size:13px; color:#64748B; line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.stop()


# ─── Main Analysis View ───────────────────────────────────────────────────────
data = st.session_state.data
ticker = st.session_state.ticker
info = st.session_state.info
bm_data = st.session_state.benchmark
rf = st.session_state.rf

close = get_close_prices(data)
bm_close = get_close_prices(bm_data) if bm_data is not None else None

metrics = compute_all_metrics(close, bm_close, rf)
daily_returns = compute_daily_returns(close)
mas = compute_moving_averages(close)

# ── Header ────────────────────────────────────────────────────────────────────
company_name = info.get("longName", ticker)
sector = info.get("sector", "—")
industry = info.get("industry", "—")
market_cap = info.get("marketCap", None)
exchange = info.get("exchange", "—")

current_price = float(close.iloc[-1])
prev_price = float(close.iloc[-2]) if len(close) > 1 else current_price
day_chg = current_price - prev_price
day_chg_pct = (day_chg / prev_price) * 100
is_up = day_chg >= 0
chg_color = "#10B981" if is_up else "#EF4444"
chg_sign = "+" if is_up else ""
badge_cls = "badge-up" if is_up else "badge-down"
arrow = "▲" if is_up else "▼"

cap_str = ""
if market_cap:
    if market_cap >= 1e12:
        cap_str = f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        cap_str = f"${market_cap/1e9:.2f}B"
    else:
        cap_str = f"${market_cap/1e6:.0f}M"

st.markdown(
    f"""
    <div class="hero-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
            <div>
                <div style="font-size:26px; font-weight:700; color:#E2E8F0;">
                    {company_name}
                    <span style="font-size:16px; color:#64748B; font-weight:400; margin-left:8px;">({ticker})</span>
                </div>
                <div style="margin-top:6px; font-size:13px; color:#64748B;">
                    {exchange} &nbsp;·&nbsp; {sector} &nbsp;·&nbsp; {industry}
                    {"&nbsp;·&nbsp; Mkt Cap: " + cap_str if cap_str else ""}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:38px; font-weight:700; color:#E2E8F0; line-height:1.1;">
                    ${current_price:,.2f}
                </div>
                <div style="font-size:16px; color:{chg_color}; margin-top:4px;">
                    {arrow} {chg_sign}{day_chg:.2f} ({chg_sign}{day_chg_pct:.2f}%) <span style="font-size:12px; color:#64748B;">1D</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_tech, tab_risk, tab_compare = st.tabs(
    ["📊  Overview", "📈  Technical", "📉  Risk Analysis", "⚖️  Compare"]
)


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # Row 1: core metrics
    c1, c2, c3, c4 = st.columns(4)
    sr = metrics["sharpe_ratio"]
    sr_label = "Excellent" if sr > 2 else "Good" if sr > 1 else "Fair" if sr > 0 else "Poor"
    with c1:
        st.metric("Sharpe Ratio", f"{sr:.3f}", delta=sr_label,
                  help="(Annualized Return − Risk-Free Rate) / Annualized Volatility")
    with c2:
        ann_ret = metrics["annualized_return"] * 100
        st.metric("Ann. Return (CAGR)", f"{ann_ret:+.2f}%",
                  delta=f"Total: {metrics['total_return']*100:+.1f}%",
                  help="Compound Annual Growth Rate over the selected period")
    with c3:
        st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%",
                  help="Worst peak-to-trough loss in the period")
    with c4:
        ann_vol = metrics["annualized_volatility"] * 100
        st.metric("Ann. Volatility", f"{ann_vol:.2f}%",
                  help="Daily return std-dev × √252")

    st.divider()

    # Price chart
    st.plotly_chart(
        plot_price_chart(close, data, mas, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.divider()

    # Row 2: secondary metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        beta = metrics.get("beta")
        st.metric("Beta (vs SPY)", f"{beta:.3f}" if beta is not None else "N/A",
                  help="Sensitivity to S&P 500 (SPY) market moves")
    with c2:
        alpha = metrics.get("alpha")
        st.metric("Jensen's Alpha", f"{alpha*100:+.2f}%" if alpha is not None else "N/A",
                  help="Excess return above CAPM expectation (annualized)")
    with c3:
        sortino = metrics["sortino_ratio"]
        st.metric("Sortino Ratio", f"{sortino:.3f}",
                  help="Like Sharpe but only penalises downside volatility")
    with c4:
        calmar = metrics["calmar_ratio"]
        st.metric("Calmar Ratio", f"{calmar:.3f}",
                  help="Annualized Return / |Max Drawdown|")

    st.divider()

    # Rolling Sharpe
    st.markdown("#### 📐 Rolling Sharpe Ratio (63-day window)")
    st.plotly_chart(
        plot_rolling_sharpe(close, ticker, rf, window=63),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Technical Analysis
# ════════════════════════════════════════════════════════════════════════════
with tab_tech:
    # Candlestick
    st.markdown("#### 🕯️ Candlestick Chart")
    st.plotly_chart(
        plot_candlestick(data, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.divider()

    # RSI
    st.markdown("#### 📡 Relative Strength Index (RSI-14)")
    rsi_series = compute_rsi(close)
    last_rsi = rsi_series.dropna().iloc[-1]
    rsi_interp = "🔴 Overbought (>70)" if last_rsi > 70 else "🟢 Oversold (<30)" if last_rsi < 30 else "⚪ Neutral"
    st.caption(f"Current RSI: **{last_rsi:.1f}** — {rsi_interp}")
    st.plotly_chart(
        plot_rsi_chart(close, rsi_series, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.divider()

    # Bollinger Bands
    st.markdown("#### 🎯 Bollinger Bands (SMA-20, ±2σ)")
    bb_ma, bb_upper, bb_lower = compute_bollinger_bands(close)
    last_price = close.iloc[-1]
    last_upper = bb_upper.dropna().iloc[-1]
    last_lower = bb_lower.dropna().iloc[-1]
    bb_pct = (last_price - last_lower) / (last_upper - last_lower) if (last_upper - last_lower) != 0 else 0.5
    st.caption(f"%B (Band Position): **{bb_pct*100:.1f}%** — 0% = lower band, 100% = upper band")
    st.plotly_chart(
        plot_bollinger_chart(close, bb_ma, bb_upper, bb_lower, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Risk Analysis
# ════════════════════════════════════════════════════════════════════════════
with tab_risk:
    var_95 = metrics["var_95"]
    ann_vol = metrics["annualized_volatility"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("VaR (95%, 1-day)", f"{var_95*100:.2f}%",
                  help="Historical: on 95% of days, loss ≤ this value")
    with c2:
        st.metric("VaR (99%, 1-day)",
                  f"{float(__import__('numpy').percentile(daily_returns, 1))*100:.2f}%",
                  help="Historical VaR at 99% confidence")
    with c3:
        st.metric("Skewness", f"{float(daily_returns.skew()):.3f}",
                  help="Negative = left-tail risk (more large losses than gains)")
    with c4:
        st.metric("Kurtosis (excess)", f"{float(daily_returns.kurtosis()):.3f}",
                  help="Fat tails indicator. Normal distribution = 0")

    st.divider()

    # Drawdown chart
    st.markdown("#### 📉 Historical Drawdown")
    drawdown = compute_drawdown_series(close)
    st.plotly_chart(
        plot_drawdown(drawdown, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.divider()

    # Returns distribution
    st.markdown("#### 📊 Daily Returns Distribution")
    st.plotly_chart(
        plot_returns_distribution(daily_returns, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Key stats table
    st.divider()
    st.markdown("#### 📋 Full Metrics Summary")
    summary_data = {
        "Metric": [
            "Total Return", "Ann. Return (CAGR)", "Ann. Volatility",
            "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio",
            "Max Drawdown", "VaR (95%)", "Beta (vs SPY)", "Jensen's Alpha",
            "Skewness", "Kurtosis (excess)", "Trading Days"
        ],
        "Value": [
            f"{metrics['total_return']*100:+.2f}%",
            f"{metrics['annualized_return']*100:+.2f}%",
            f"{metrics['annualized_volatility']*100:.2f}%",
            f"{metrics['sharpe_ratio']:.4f}",
            f"{metrics['sortino_ratio']:.4f}",
            f"{metrics['calmar_ratio']:.4f}",
            f"{metrics['max_drawdown']*100:.2f}%",
            f"{metrics['var_95']*100:.2f}%",
            f"{metrics['beta']:.4f}" if metrics.get("beta") is not None else "N/A",
            f"{metrics['alpha']*100:+.2f}%" if metrics.get("alpha") is not None else "N/A",
            f"{float(daily_returns.skew()):.4f}",
            f"{float(daily_returns.kurtosis()):.4f}",
            str(len(close)),
        ],
        "Formula": [
            "(P_end / P_start) − 1",
            "(1 + R_total)^(252/N) − 1",
            "σ_daily × √252",
            "(R_p − R_f) / σ_p",
            "(R_p − R_f) / σ_downside",
            "R_ann / |MaxDD|",
            "min(P_t / max(P_0..t) − 1)",
            "5th percentile of daily returns",
            "Cov(R_s, R_m) / Var(R_m)",
            "R_s − [R_f + β(R_m − R_f)]",
            "3rd standardised moment",
            "4th standardised moment − 3",
            "Count of trading days",
        ],
    }
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(
        df_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="small"),
            "Formula": st.column_config.TextColumn("Formula / Definition", width="large"),
        },
    )


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Comparison
# ════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown("#### ⚖️ Multi-Ticker Comparison")
    st.caption("Compare the main ticker against up to 2 additional symbols.")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        cmp1 = st.text_input("Ticker 2", placeholder="e.g. TSLA", key="cmp1").upper().strip()
    with col_t2:
        cmp2 = st.text_input("Ticker 3", placeholder="e.g. SPY",  key="cmp2").upper().strip()

    if st.button("⚖️  Compare", type="primary", key="compare_btn"):
        extra = [t for t in [cmp1, cmp2] if t]
        if not extra:
            st.info("Enter at least one additional ticker above.")
        else:
            all_data = {ticker: data}
            with st.spinner("Fetching comparison data…"):
                for sym in extra:
                    d = fetch_stock_data(sym, str(st.session_state.start), str(st.session_state.end))
                    if d is not None:
                        all_data[sym] = d
                    else:
                        st.warning(f"Could not fetch data for **{sym}** — skipping.")

            if len(all_data) > 1:
                st.plotly_chart(
                    plot_comparison_chart(all_data),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

                # Comparison metrics table
                st.divider()
                st.markdown("#### 📋 Metrics Comparison")
                rows = []
                for sym, df in all_data.items():
                    p = get_close_prices(df)
                    m = compute_all_metrics(p, bm_close, rf)
                    rows.append({
                        "Ticker":       sym,
                        "Ann. Return":  f"{m['annualized_return']*100:+.2f}%",
                        "Volatility":   f"{m['annualized_volatility']*100:.2f}%",
                        "Sharpe":       f"{m['sharpe_ratio']:.3f}",
                        "Sortino":      f"{m['sortino_ratio']:.3f}",
                        "Max DD":       f"{m['max_drawdown']*100:.2f}%",
                        "Calmar":       f"{m['calmar_ratio']:.3f}",
                        "VaR 95%":      f"{m['var_95']*100:.2f}%",
                        "Beta":         f"{m['beta']:.3f}" if m.get("beta") is not None else "N/A",
                        "Alpha":        f"{m['alpha']*100:+.2f}%" if m.get("alpha") is not None else "N/A",
                    })

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        # Placeholder hint
        st.markdown(
            """
            <div style="background:#131829; border:1px dashed #252D42; border-radius:14px;
                        padding:48px; text-align:center; color:#374151; margin-top:16px;">
                <div style="font-size:36px; margin-bottom:12px;">⚖️</div>
                <div style="font-size:16px; color:#64748B;">
                    Enter tickers above and click <b>Compare</b> to see a side-by-side analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
