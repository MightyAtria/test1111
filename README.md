# 📈 QuantView — US Stock Quantitative Analytics

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)
![yfinance](https://img.shields.io/badge/yfinance-0.2%2B-0D96F6)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

An introductory quantitative finance web application built with **Streamlit** and **yfinance**.  
Enter any US stock ticker, pick a time window, and get real-time quantitative metrics, technical indicators, and interactive charts — all in the browser.

---

## ✨ Features

| Category | Metrics / Charts |
|----------|-----------------|
| **Return** | Total Return, CAGR (Annualized Return) |
| **Risk** | Annualized Volatility, Max Drawdown, VaR (95% & 99%), Skewness, Kurtosis |
| **Risk-Adjusted** | Sharpe Ratio, Sortino Ratio, Calmar Ratio, Rolling Sharpe (63d) |
| **CAPM** | Beta (vs SPY), Jensen's Alpha |
| **Technical** | RSI-14, Bollinger Bands (20, 2σ), MA20 / MA50 / MA200 |
| **Visualization** | Price + Volume, Candlestick, Drawdown, Returns Distribution, Multi-ticker Comparison |

---

## 📐 Key Formulas

### Sharpe Ratio
```
SR = (R_p - R_f) / σ_p
```
- `R_p` = annualized portfolio return  
- `R_f` = risk-free rate (configurable, default 4.5%)  
- `σ_p` = annualized standard deviation of returns

### Sortino Ratio
```
Sortino = (R_p - R_f) / σ_downside
```
Only penalises returns **below** the target (downside deviation), unlike Sharpe which penalises all volatility.

### Maximum Drawdown
```
MaxDD = min( P_t / max(P_0 … P_t) - 1 )
```
Worst peak-to-trough percentage loss over the period.

### Beta & Jensen's Alpha (CAPM)
```
Beta  = Cov(R_stock, R_market) / Var(R_market)
Alpha = R_stock_ann - [ R_f + β × (R_market_ann - R_f) ]
```
Benchmark: **SPY** (S&P 500 ETF).

### Value at Risk (Historical, 95%)
```
VaR_95 = 5th percentile of daily return distribution
```

---

## 🚀 Local Installation

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/stock-analysis-app.git
cd stock-analysis-app

# 2. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501** automatically.

---

## 🖥️ Usage

1. **Enter a ticker** in the left sidebar (e.g. `AAPL`, `TSLA`, `NVDA`, `SPY`)
2. **Select a time range**: 1M / 3M / 6M / 1Y / 2Y / 5Y or Custom
3. **Adjust the Risk-Free Rate** slider (default 4.5%)
4. Click **🔍 Analyze**
5. Browse the four tabs:
   - **📊 Overview** — Key KPIs + price chart + rolling Sharpe
   - **📈 Technical** — Candlestick + RSI + Bollinger Bands
   - **📉 Risk Analysis** — Drawdown + returns distribution + full metrics table
   - **⚖️ Compare** — Normalized return comparison for up to 3 tickers

---

## 🌐 Self-Hosted Deployment (Public Domain via Nginx)

### 1. Run Streamlit as a background service

**Windows (NSSM):**
```powershell
winget install nssm
nssm install StockApp "C:\Python311\Scripts\streamlit.exe" `
    "run C:\path\to\app.py --server.port 8501 --server.headless true"
nssm start StockApp
```

**Linux (systemd):**
```ini
# /etc/systemd/system/stockapp.service
[Unit]
Description=QuantView Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stock-analysis-app
ExecStart=/home/ubuntu/.venv/bin/streamlit run app.py \
          --server.port 8501 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now stockapp
```

### 2. Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name stock.yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

### 3. HTTPS via Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d stock.yourdomain.com
```

### 4. Router port forwarding
Forward external ports **80/443** → machine's local IP → port **80**.  
Set your machine to a **static LAN IP** to avoid re-configuration after router restarts.  
Point the domain's **DNS A record** to your router's public IP.

---

## 🗂️ Project Structure

```
stock-analysis-app/
├── app.py                 # Streamlit entry point
├── src/
│   ├── data_fetcher.py    # yfinance data retrieval + caching
│   ├── metrics.py         # All quantitative calculations
│   └── charts.py          # Plotly chart builders
├── .streamlit/
│   └── config.toml        # Dark theme + server settings
├── deploy/
│   └── nginx.conf         # Production Nginx config template
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚠️ Disclaimer

> This application is built **for educational purposes only**.  
> It is **not** financial advice and should **not** be used for real investment decisions.  
> All data is sourced from Yahoo Finance via `yfinance` and may be delayed or inaccurate.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
