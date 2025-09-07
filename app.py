import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from io import StringIO

st.set_page_config(page_title="PEGY Stock Screener", page_icon="📈", layout="wide")

# ---- Header ----
st.title("📈 PEGY Stock Screener")
st.caption("PEGY = P/E ÷ (EPS Growth % + Dividend Yield %) — lower is generally better.")

with st.expander("What is PEGY?"):
    st.markdown(
        '''
        **PEGY** adjusts the classic P/E by adding dividend yield to earnings growth.  
        
        **Formula:**  
        
        `PEGY = (P/E) / (g + y)`  
        where **g** is expected annual EPS growth (%) and **y** is dividend yield (%).  
        
        *Rule of thumb:* PEGY < 1.0 can suggest attractive value *(not investment advice)*.
        '''
    )

# ---- Sidebar Inputs ----
st.sidebar.header("Inputs")
tickers_text = st.sidebar.text_area(
    "Tickers (comma or newline separated)",
    value="AAPL, MSFT, KO, TSLA",
    height=96
)

growth_source = st.sidebar.selectbox(
    "Growth source",
    [
        "Analyst 5y EPS growth (if available)",
        "Manual (same % for all tickers)"
    ],
    index=0
)

manual_growth = st.sidebar.number_input(
    "Manual growth % (used if selected above)",
    min_value=0.0, max_value=100.0, value=10.0, step=0.5
)

pe_type = st.sidebar.selectbox("P/E type", ["Forward PE", "Trailing PE"], index=0)

min_div_yield = st.sidebar.number_input("Min Dividend Yield % (filter)", 0.0, 20.0, 0.0, 0.5)
max_pegy = st.sidebar.number_input("Max PEGY (filter)", 0.0, 5.0, 1.5, 0.1)

st.sidebar.markdown("---")

def parse_tickers(txt: str):
    raw = [x.strip().upper() for x in txt.replace("\n", ",").split(",")]
    return [t for t in raw if t]

tickers = parse_tickers(tickers_text)

@st.cache_data(show_spinner=False, ttl=60*15)
def fetch_summary(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info if hasattr(t, "info") else {}
    # PE
    trailing_pe = info.get("trailingPE", np.nan)
    forward_pe = info.get("forwardPE", np.nan)
    # Dividend yield as fraction in yfinance (e.g., 0.0123) -> convert to %
    div_yield = info.get("dividendYield", 0.0)
    if div_yield is None:
        div_yield = 0.0
    div_yield_pct = float(div_yield) * 100.0

    # Try analyst 5y EPS growth % (if available)
    growth_pct = np.nan
    try:
        analysis = t.analysis
        if analysis is not None and "+5y" in analysis.columns:
            val = analysis["+5y"].dropna()
            if len(val) > 0:
                growth_pct = float(val.iloc[0]) * 100.0
    except Exception:
        pass

    name = info.get("shortName") or info.get("longName") or ticker
    price = info.get("currentPrice") or info.get("regularMarketPrice") or np.nan
    sector = info.get("sector") or ""
    return {
        "Ticker": ticker,
        "Name": name,
        "Price": price,
        "Sector": sector,
        "Trailing PE": trailing_pe,
        "Forward PE": forward_pe,
        "Dividend %": div_yield_pct,
        "Analyst 5y Growth %": growth_pct
    }

@st.cache_data(show_spinner=True, ttl=60*15)
def batch_fetch(tickers: list[str]) -> pd.DataFrame:
    rows = []
    for t in tickers:
        try:
            rows.append(fetch_summary(t))
        except Exception as e:
            rows.append({"Ticker": t, "Error": str(e)})
    return pd.DataFrame(rows)

if st.sidebar.button("Run Screen", type="primary"):
    if not tickers:
        st.warning("Please provide at least one ticker.")
        st.stop()

    df = batch_fetch(tickers)

    # Choose PE
    pe_col = "Forward PE" if pe_type == "Forward PE" else "Trailing PE"
    df["PE Used"] = df[pe_col]

    # Choose growth
    if growth_source.startswith("Analyst"):
        df["Growth % Used"] = df["Analyst 5y Growth %"]
        # Fallback to manual if missing
        df["Growth % Used"] = df["Growth % Used"].fillna(manual_growth)
    else:
        df["Growth % Used"] = manual_growth

    # Clean negative/zero cases
    df["Dividend %"] = df["Dividend %"].clip(lower=0.0)
    df["Growth % Used"] = df["Growth % Used"].clip(lower=0.0)

    # Avoid divide-by-zero
    denom = df["Growth % Used"] + df["Dividend %"]
    df["PEGY"] = df["PE Used"] / denom.replace({0: np.nan})

    # Filters
    filtered = df.copy()
    if min_div_yield > 0:
        filtered = filtered[filtered["Dividend %"] >= min_div_yield]
    if max_pegy > 0:
        filtered = filtered[filtered["PEGY"] <= max_pegy]

    # Sort by PEGY ascending (best first)
    filtered = filtered.sort_values(by=["PEGY", "Ticker"], na_position="last", ascending=[True, True])

    # Display
    st.subheader("Results")
    st.dataframe(
        filtered[["Ticker", "Name", "Sector", "Price", "PE Used", "Growth % Used", "Dividend %", "PEGY"]]
        .round({"Price": 2, "PE Used": 2, "Growth % Used": 2, "Dividend %": 2, "PEGY": 2}),
        use_container_width=True
    )

    # Download
    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="pegy_screen.csv", mime="text/csv")

    # Notes
    st.info(
        "Notes: Data from Yahoo Finance via yfinance. Analyst growth may be unavailable for some tickers; the tool falls back to your manual growth %. "
        "PEGY is a heuristic, not investment advice. Verify fundamentals before making decisions."
    )
else:
    st.write("Enter tickers in the sidebar and tap **Run Screen**. On iPhone/Android, open this app URL and **Add to Home Screen** for an app-like experience.")