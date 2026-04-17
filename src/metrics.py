"""
metrics.py
All quantitative finance calculations.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


# ─── Low-level helpers ────────────────────────────────────────────────────────

def compute_daily_returns(prices: pd.Series) -> pd.Series:
    """Simple daily percentage returns."""
    return prices.pct_change().dropna()


def compute_annualized_return(prices: pd.Series) -> float:
    """Compound annualized growth rate (CAGR)."""
    if len(prices) < 2:
        return 0.0
    total_return = prices.iloc[-1] / prices.iloc[0] - 1
    n_days = len(prices)
    return (1 + total_return) ** (252 / n_days) - 1


def compute_annualized_volatility(daily_returns: pd.Series) -> float:
    """Annualized standard deviation of daily returns."""
    return float(daily_returns.std() * np.sqrt(252))


# ─── Risk-adjusted return metrics ─────────────────────────────────────────────

def compute_sharpe_ratio(daily_returns: pd.Series, rf: float = 0.045) -> float:
    """
    Sharpe Ratio = (R_p - R_f) / σ_p
    Both R_p and σ_p are annualized.
    """
    ann_return = (1 + daily_returns.mean()) ** 252 - 1
    ann_vol = compute_annualized_volatility(daily_returns)
    if ann_vol == 0:
        return 0.0
    return float((ann_return - rf) / ann_vol)


def compute_sortino_ratio(daily_returns: pd.Series, rf: float = 0.045) -> float:
    """
    Sortino Ratio = (R_p - R_f) / σ_downside
    Uses only below-target returns for the denominator.
    """
    ann_return = (1 + daily_returns.mean()) ** 252 - 1
    daily_rf = (1 + rf) ** (1 / 252) - 1
    downside = daily_returns[daily_returns < daily_rf]
    if len(downside) == 0:
        return 0.0
    downside_std = float(np.sqrt(np.mean(downside ** 2)) * np.sqrt(252))
    if downside_std == 0:
        return 0.0
    return float((ann_return - rf) / downside_std)


def compute_calmar_ratio(prices: pd.Series) -> float:
    """Calmar Ratio = Annualized Return / |Max Drawdown|"""
    ann_return = compute_annualized_return(prices)
    max_dd = compute_max_drawdown(prices)
    if max_dd == 0:
        return 0.0
    return float(ann_return / abs(max_dd))


# ─── Drawdown ─────────────────────────────────────────────────────────────────

def compute_max_drawdown(prices: pd.Series) -> float:
    """Peak-to-trough maximum drawdown (negative value)."""
    roll_max = prices.cummax()
    drawdown = prices / roll_max - 1
    return float(drawdown.min())


def compute_drawdown_series(prices: pd.Series) -> pd.Series:
    """Full drawdown time series (for plotting)."""
    roll_max = prices.cummax()
    return prices / roll_max - 1


# ─── CAPM metrics ─────────────────────────────────────────────────────────────

def compute_beta_alpha(
    stock_returns: pd.Series,
    market_returns: pd.Series,
    rf: float = 0.045,
) -> Tuple[float, float]:
    """
    Beta  = Cov(R_stock, R_market) / Var(R_market)
    Alpha = R_stock_ann - [R_f + Beta * (R_market_ann - R_f)]  (Jensen's Alpha)
    """
    aligned = pd.concat([stock_returns, market_returns], axis=1).dropna()
    aligned.columns = ["stock", "market"]

    cov_matrix = np.cov(aligned["stock"], aligned["market"])
    beta = float(cov_matrix[0, 1] / cov_matrix[1, 1])

    ann_stock = (1 + aligned["stock"].mean()) ** 252 - 1
    ann_market = (1 + aligned["market"].mean()) ** 252 - 1
    alpha = float(ann_stock - (rf + beta * (ann_market - rf)))

    return beta, alpha


# ─── Value at Risk ────────────────────────────────────────────────────────────

def compute_var(daily_returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical VaR at given confidence level (negative value)."""
    return float(np.percentile(daily_returns, (1 - confidence) * 100))


# ─── Technical indicators ─────────────────────────────────────────────────────

def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def compute_bollinger_bands(
    prices: pd.Series, window: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Returns (middle_band, upper_band, lower_band).
    Middle = SMA(window), bands = middle ± num_std * rolling_std
    """
    ma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return ma, upper, lower


def compute_moving_averages(prices: pd.Series, periods=(20, 50, 200)) -> dict:
    """Returns {f'MA{p}': series} for each period, only when enough data."""
    result = {}
    for p in periods:
        if len(prices) >= p:
            result[f"MA{p}"] = prices.rolling(window=p).mean()
    return result


# ─── Aggregate calculator ──────────────────────────────────────────────────────

def compute_all_metrics(
    prices: pd.Series,
    market_prices: Optional[pd.Series] = None,
    rf: float = 0.045,
) -> dict:
    """Compute the full set of quantitative metrics for display."""
    daily_returns = compute_daily_returns(prices)

    metrics: dict = {
        "total_return": float(prices.iloc[-1] / prices.iloc[0] - 1),
        "annualized_return": compute_annualized_return(prices),
        "annualized_volatility": compute_annualized_volatility(daily_returns),
        "sharpe_ratio": compute_sharpe_ratio(daily_returns, rf),
        "sortino_ratio": compute_sortino_ratio(daily_returns, rf),
        "calmar_ratio": compute_calmar_ratio(prices),
        "max_drawdown": compute_max_drawdown(prices),
        "var_95": compute_var(daily_returns, 0.95),
        "beta": None,
        "alpha": None,
    }

    if market_prices is not None and len(market_prices) > 10:
        market_returns = compute_daily_returns(market_prices)
        try:
            beta, alpha = compute_beta_alpha(daily_returns, market_returns, rf)
            metrics["beta"] = beta
            metrics["alpha"] = alpha
        except Exception:
            pass

    return metrics
