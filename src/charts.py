"""
charts.py
All Plotly chart builders. Every function returns a go.Figure
ready to be passed to st.plotly_chart().
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats

# ─── Design tokens ────────────────────────────────────────────────────────────
BG = "#0A0E1A"
PAPER = "#131829"
GRID = "#1E2740"
TEXT = "#94A3B8"
TEXT_BRIGHT = "#E2E8F0"

C = {
    "price": "#6366F1",
    "area": "rgba(99,102,241,0.15)",
    "ma20": "#F59E0B",
    "ma50": "#3B82F6",
    "ma200": "#EC4899",
    "up": "#10B981",
    "down": "#EF4444",
    "volume": "rgba(99,102,241,0.3)",
    "bb_band": "rgba(148,163,184,0.4)",
    "bb_fill": "rgba(99,102,241,0.08)",
    "rsi": "#F59E0B",
    "drawdown": "#EF4444",
    "drawdown_fill": "rgba(239,68,68,0.2)",
    "normal": "rgba(99,102,241,0.5)",
    "hist": "#6366F1",
    "compare": ["#6366F1", "#10B981", "#F59E0B", "#EC4899"],
}

PALETTE = [C["compare"][i % 4] for i in range(10)]


def _base_layout(**kwargs) -> dict:
    """Shared Plotly layout defaults."""
    base = dict(
        paper_bgcolor=PAPER,
        plot_bgcolor=BG,
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        xaxis=dict(
            gridcolor=GRID,
            zerolinecolor=GRID,
            showspikes=True,
            spikecolor=TEXT,
            spikethickness=1,
        ),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(
            bgcolor="rgba(19,24,41,0.8)",
            bordercolor=GRID,
            borderwidth=1,
            font=dict(color=TEXT_BRIGHT),
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1C2236", bordercolor=GRID, font_color=TEXT_BRIGHT),
        margin=dict(l=60, r=20, t=50, b=40),
    )
    base.update(kwargs)
    return base


# ─── 1. Price Chart (area + moving averages) ──────────────────────────────────

def plot_price_chart(
    prices: pd.Series,
    ohlcv: pd.DataFrame,
    moving_averages: dict,
    ticker: str,
) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # Area fill under price
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=prices.values,
            mode="lines",
            name=ticker,
            line=dict(color=C["price"], width=2),
            fill="tozeroy",
            fillcolor=C["area"],
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # Moving averages
    ma_colors = {"MA20": C["ma20"], "MA50": C["ma50"], "MA200": C["ma200"]}
    for name, series in moving_averages.items():
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=name,
                line=dict(color=ma_colors.get(name, TEXT), width=1.2, dash="dot"),
                hovertemplate=f"{name}: $%{{y:.2f}}<extra></extra>",
            ),
            row=1, col=1,
        )

    # Volume bars
    if "Volume" in ohlcv.columns:
        close = ohlcv["Close"] if "Close" in ohlcv.columns else prices
        open_ = ohlcv["Open"] if "Open" in ohlcv.columns else prices
        vol_colors = [
            C["up"] if c >= o else C["down"]
            for c, o in zip(close.values, open_.values)
        ]
        fig.add_trace(
            go.Bar(
                x=ohlcv.index,
                y=ohlcv["Volume"].values,
                name="Volume",
                marker_color=vol_colors,
                marker_opacity=0.6,
                hovertemplate="Volume: %{y:,.0f}<extra></extra>",
            ),
            row=2, col=1,
        )

    layout = _base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — Price & Volume",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        xaxis2=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickprefix="$"),
        yaxis2=dict(gridcolor=GRID, zerolinecolor=GRID, title="Volume"),
    )
    fig.update_layout(**layout)
    return fig


# ─── 2. Candlestick Chart ─────────────────────────────────────────────────────

def plot_candlestick(ohlcv: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure(
        go.Candlestick(
            x=ohlcv.index,
            open=ohlcv["Open"],
            high=ohlcv["High"],
            low=ohlcv["Low"],
            close=ohlcv["Close"],
            name=ticker,
            increasing_line_color=C["up"],
            decreasing_line_color=C["down"],
        )
    )
    fig.update_layout(
        **_base_layout(
            title=dict(
                text=f"<b>{ticker}</b> — Candlestick",
                font=dict(color=TEXT_BRIGHT, size=16),
                x=0.02,
            ),
            xaxis_rangeslider_visible=False,
            yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickprefix="$"),
        )
    )
    return fig


# ─── 3. RSI Chart ─────────────────────────────────────────────────────────────

def plot_rsi_chart(prices: pd.Series, rsi: pd.Series, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.45],
        vertical_spacing=0.05,
    )

    # Price line (top)
    fig.add_trace(
        go.Scatter(
            x=prices.index, y=prices.values,
            mode="lines", name="Price",
            line=dict(color=C["price"], width=1.8),
            hovertemplate="Price: $%{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # RSI (bottom)
    fig.add_trace(
        go.Scatter(
            x=rsi.index, y=rsi.values,
            mode="lines", name="RSI(14)",
            line=dict(color=C["rsi"], width=2),
            hovertemplate="RSI: %{y:.1f}<extra></extra>",
        ),
        row=2, col=1,
    )

    # Overbought / oversold zones
    for level, color, label in [(70, "rgba(239,68,68,0.15)", "Overbought"),
                                  (30, "rgba(16,185,129,0.15)", "Oversold")]:
        fig.add_hline(
            y=level, row=2, col=1,
            line=dict(color=TEXT, width=1, dash="dot"),
            annotation_text=label,
            annotation_font_color=TEXT,
            annotation_position="top right",
        )

    # Fill overbought zone
    fig.add_hrect(y0=70, y1=100, row=2, col=1, fillcolor="rgba(239,68,68,0.07)", line_width=0)
    fig.add_hrect(y0=0, y1=30, row=2, col=1, fillcolor="rgba(16,185,129,0.07)", line_width=0)

    layout = _base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — RSI (14-day)",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickprefix="$"),
        yaxis2=dict(gridcolor=GRID, zerolinecolor=GRID, range=[0, 100], title="RSI"),
        xaxis2=dict(gridcolor=GRID, zerolinecolor=GRID),
    )
    fig.update_layout(**layout)
    return fig


# ─── 4. Bollinger Bands ───────────────────────────────────────────────────────

def plot_bollinger_chart(
    prices: pd.Series,
    bb_ma: pd.Series,
    bb_upper: pd.Series,
    bb_lower: pd.Series,
    ticker: str,
) -> go.Figure:
    fig = go.Figure()

    # Fill between bands
    fig.add_trace(go.Scatter(
        x=pd.concat([bb_upper, bb_lower[::-1]]).index,
        y=pd.concat([bb_upper, bb_lower[::-1]]).values,
        fill="toself",
        fillcolor=C["bb_fill"],
        line=dict(color="rgba(0,0,0,0)"),
        name="BB Band",
        hoverinfo="skip",
        showlegend=False,
    ))

    # Upper / lower bands
    for band, name in [(bb_upper, "Upper Band"), (bb_lower, "Lower Band")]:
        fig.add_trace(go.Scatter(
            x=band.index, y=band.values,
            mode="lines", name=name,
            line=dict(color=C["bb_band"], width=1, dash="dash"),
            hovertemplate=f"{name}: $%{{y:.2f}}<extra></extra>",
        ))

    # Middle band (SMA20)
    fig.add_trace(go.Scatter(
        x=bb_ma.index, y=bb_ma.values,
        mode="lines", name="SMA(20)",
        line=dict(color=C["ma20"], width=1.5),
        hovertemplate="SMA20: $%{y:.2f}<extra></extra>",
    ))

    # Price
    fig.add_trace(go.Scatter(
        x=prices.index, y=prices.values,
        mode="lines", name="Price",
        line=dict(color=C["price"], width=2),
        hovertemplate="Price: $%{y:.2f}<extra></extra>",
    ))

    fig.update_layout(**_base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — Bollinger Bands (20, 2σ)",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickprefix="$"),
    ))
    return fig


# ─── 5. Drawdown Chart ────────────────────────────────────────────────────────

def plot_drawdown(drawdown: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=drawdown.index,
        y=(drawdown * 100).values,
        mode="lines",
        name="Drawdown",
        line=dict(color=C["drawdown"], width=2),
        fill="tozeroy",
        fillcolor=C["drawdown_fill"],
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Drawdown: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(**_base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — Historical Drawdown",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor=TEXT,
            zerolinewidth=1,
            ticksuffix="%",
            title="Drawdown (%)",
        ),
    ))
    return fig


# ─── 6. Returns Distribution ──────────────────────────────────────────────────

def plot_returns_distribution(daily_returns: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=(daily_returns * 100).values,
        nbinsx=60,
        name="Daily Returns",
        marker_color=C["hist"],
        marker_opacity=0.7,
        histnorm="probability density",
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.4f}<extra></extra>",
    ))

    # Fitted normal distribution overlay
    mu = daily_returns.mean() * 100
    sigma = daily_returns.std() * 100
    x_range = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 300)
    y_norm = scipy_stats.norm.pdf(x_range, mu, sigma)

    fig.add_trace(go.Scatter(
        x=x_range, y=y_norm,
        mode="lines",
        name="Normal Fit",
        line=dict(color=C["normal"], width=2.5),
    ))

    # VaR line
    var_95 = np.percentile(daily_returns * 100, 5)
    fig.add_vline(
        x=var_95,
        line=dict(color=C["down"], width=2, dash="dash"),
        annotation_text=f"VaR 95%: {var_95:.2f}%",
        annotation_font_color=C["down"],
        annotation_position="top right",
    )

    fig.update_layout(**_base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — Daily Returns Distribution",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, title="Probability Density"),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, ticksuffix="%", title="Daily Return (%)"),
        bargap=0.02,
        hovermode="x",
    ))
    return fig


# ─── 7. Multi-Ticker Comparison ───────────────────────────────────────────────

def plot_comparison_chart(data_dict: dict) -> go.Figure:
    """
    Normalized cumulative return chart.
    All tickers start at 100 for easy comparison.
    """
    fig = go.Figure()

    for i, (ticker, df) in enumerate(data_dict.items()):
        # Get close prices
        for col in ("Close", "Adj Close"):
            if col in df.columns:
                prices = df[col].dropna()
                break
        else:
            prices = df.select_dtypes("number").iloc[:, 0].dropna()

        normalized = (prices / prices.iloc[0]) * 100

        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode="lines",
            name=ticker,
            line=dict(color=PALETTE[i], width=2.2),
            hovertemplate=f"<b>{ticker}</b><br>%{{x|%Y-%m-%d}}<br>Return Index: %{{y:.1f}}<extra></extra>",
        ))

    # Baseline at 100
    fig.add_hline(y=100, line=dict(color=TEXT, width=1, dash="dot"))

    fig.update_layout(**_base_layout(
        title=dict(
            text="<b>Normalized Return Comparison</b>  (Base = 100)",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor=GRID,
            title="Return Index (Base 100)",
        ),
    ))
    return fig


# ─── 8. Rolling Sharpe Ratio ──────────────────────────────────────────────────

def plot_rolling_sharpe(prices: pd.Series, ticker: str, rf: float = 0.045, window: int = 63) -> go.Figure:
    """Rolling Sharpe Ratio over a ~1-quarter (63-day) window."""
    daily_returns = prices.pct_change().dropna()
    daily_rf = (1 + rf) ** (1 / 252) - 1
    excess = daily_returns - daily_rf

    rolling_mean = excess.rolling(window).mean() * 252
    rolling_std = daily_returns.rolling(window).std() * np.sqrt(252)
    rolling_sharpe = rolling_mean / rolling_std

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rolling_sharpe.index,
        y=rolling_sharpe.values,
        mode="lines",
        name=f"Rolling Sharpe ({window}d)",
        line=dict(color=C["price"], width=2),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.1)",
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Sharpe: %{y:.2f}<extra></extra>",
    ))

    fig.add_hline(y=0, line=dict(color=TEXT, width=1, dash="dot"))
    fig.add_hline(y=1, line=dict(color=C["up"], width=1, dash="dot"),
                  annotation_text="SR = 1", annotation_font_color=C["up"])

    fig.update_layout(**_base_layout(
        title=dict(
            text=f"<b>{ticker}</b> — Rolling Sharpe Ratio ({window}-day window)",
            font=dict(color=TEXT_BRIGHT, size=16),
            x=0.02,
        ),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, title="Sharpe Ratio"),
    ))
    return fig
