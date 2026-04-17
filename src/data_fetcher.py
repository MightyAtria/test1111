"""
data_fetcher.py
Handles all yfinance data retrieval with caching.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional

BENCHMARK_TICKER = "SPY"


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a single ticker.
    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    Returns None on failure or if no data is found.
    """
    try:
        data = yf.download(
            ticker.upper().strip(),
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if data.empty:
            return None

        # Flatten MultiIndex columns (occurs in some yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Ensure index is DatetimeIndex
        data.index = pd.to_datetime(data.index)
        return data

    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_info(ticker: str) -> dict:
    """Fetch company metadata from yfinance."""
    try:
        return yf.Ticker(ticker.upper().strip()).info
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_benchmark_data(start: str, end: str) -> Optional[pd.DataFrame]:
    """Fetch SPY benchmark data for Beta/Alpha calculations."""
    return fetch_stock_data(BENCHMARK_TICKER, start, end)


def get_close_prices(data: pd.DataFrame) -> pd.Series:
    """Extract the adjusted close price series from a DataFrame."""
    for col in ("Close", "Adj Close"):
        if col in data.columns:
            return data[col].dropna()
    # Fallback: use first numeric column
    return data.select_dtypes("number").iloc[:, 0].dropna()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_multiple_stocks(tickers: list, start: str, end: str) -> dict:
    """
    Fetch data for multiple tickers.
    Returns {ticker: DataFrame} dict (only successful fetches).
    """
    results = {}
    for ticker in tickers:
        data = fetch_stock_data(ticker, start, end)
        if data is not None:
            results[ticker] = data
    return results
