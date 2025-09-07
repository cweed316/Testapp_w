# 📈 PEGY Stock Screener (Streamlit)

A mobile-friendly web app to screen stocks by **PEGY**:
> PEGY = P/E ÷ (EPS Growth % + Dividend Yield %)

## Features
- Enter tickers (AAPL, MSFT, etc.), tap **Run Screen**
- Choose **Forward** or **Trailing** P/E
- Use **Analyst 5y EPS growth** when available (via yfinance) or a **Manual growth %** fallback
- Filter by **min dividend yield** and **max PEGY**
- Sorts by PEGY ascending; export **CSV**

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL in your mobile browser.

## Deploy Free (Two easy options)
1) **Streamlit Community Cloud**
- Go to share.streamlit.io, connect your GitHub repo containing these files, and deploy.
- Open on your phone, then **Share → Add to Home Screen** for an app-like icon.

2) **Hugging Face Spaces**
- Create a new Space (SDK: Streamlit), upload the files, and deploy.

## Notes
- yfinance sources Yahoo Finance; some tickers lack analyst 5y growth. The app falls back to your manual %.
- PEGY is a rule-of-thumb heuristic, not investment advice.