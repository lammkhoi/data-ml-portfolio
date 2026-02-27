"""
Stock Price Anomaly Detector
============================
Fetches historical stock price data from the Alpha Vantage API and flags
price anomalies using a configurable z-score threshold.

Usage:
    python stock_anomaly_detector.py

Requirements:
    pip install requests

You will need a free Alpha Vantage API key from https://www.alphavantage.co
Set it via the ALPHAVANTAGE_API_KEY environment variable, or pass it as an
argument to download_prices().
"""

import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FREQ_MAP = {
    "1": ("TIME_SERIES_DAILY",   "Time Series (Daily)"),
    "2": ("TIME_SERIES_WEEKLY",  "Weekly Time Series"),
    "3": ("TIME_SERIES_MONTHLY", "Monthly Time Series"),
}

PRICE_KEYS = {
    "1": "1. open",
    "2": "2. high",
    "3": "3. low",
    "4": "4. close",
    "5": "5. volume",
}


# ---------------------------------------------------------------------------
# Data retrieval
# ---------------------------------------------------------------------------

def download_prices(
    symbol: str,
    start_date: str,
    end_date: str,
    freq_key: str = "TIME_SERIES_DAILY",
    apikey: str = "demo",
) -> dict[str, dict[str, str]]:
    """
    Download price data from Alpha Vantage and return only dates in range.

    Parameters
    ----------
    symbol     : Ticker symbol, e.g. "AAPL"
    start_date : Inclusive start date, format "YYYY-MM-DD"
    end_date   : Inclusive end date, format "YYYY-MM-DD"
    freq_key   : Alpha Vantage function key (e.g. "TIME_SERIES_DAILY")
    apikey     : Your Alpha Vantage API key

    Returns
    -------
    dict mapping date strings to price dicts, or {} on failure
    """
    try:
        import requests
    except ImportError:
        raise ImportError("Install 'requests': pip install requests")

    outputsize = "&outputsize=full" if freq_key == "TIME_SERIES_DAILY" else ""
    url = (
        f"https://www.alphavantage.co/query"
        f"?function={freq_key}&symbol={symbol}{outputsize}&apikey={apikey}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"[ERROR] Failed to fetch data: {exc}")
        return {}

    if "Error Message" in data or "Note" in data:
        print("[ERROR] API error — check your symbol or API key.")
        return {}

    # Find the correct time-series key in the response
    ts_key = next((k for k in data if "Time Series" in k), None)
    if ts_key is None:
        print("[ERROR] Unexpected API response format.")
        return {}

    return _filter_dates(data[ts_key], start_date, end_date)


def _filter_dates(
    series: dict[str, dict[str, str]],
    start_date: str,
    end_date: str,
) -> dict[str, dict[str, str]]:
    """Return only entries whose date falls within [start_date, end_date]."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = datetime.strptime(end_date,   "%Y-%m-%d")
    return {
        date_str: price_data
        for date_str, price_data in series.items()
        if start <= datetime.strptime(date_str, "%Y-%m-%d") <= end
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(prices: dict[str, float]) -> tuple[float, float]:
    """
    Compute the mean and standard deviation of a price series.

    Parameters
    ----------
    prices : dict mapping date strings to float prices

    Returns
    -------
    (mean, std_dev)
    """
    values = list(prices.values())
    n = len(values)
    mean = sum(values) / n
    std_dev = (sum((v - mean) ** 2 for v in values) / n) ** 0.5
    return mean, std_dev


def detect_anomalies(
    prices: dict[str, float],
    mean: float,
    std_dev: float,
    k: float = 2.0,
) -> dict[str, float]:
    """
    Flag any price that deviates more than k standard deviations from the mean.

    Parameters
    ----------
    prices  : dict mapping date strings to float prices
    mean    : mean of the price series
    std_dev : standard deviation of the price series
    k       : z-score threshold (default 2.0 → ~5% flagging rate for normal data)

    Returns
    -------
    dict of {date: price} for anomalous entries
    """
    return {
        date: price
        for date, price in prices.items()
        if abs(price - mean) > k * std_dev
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Stock Price Anomaly Detector ===\n")

    symbol      = input("Ticker symbol (e.g. AAPL): ").strip().upper()
    freq_choice = input("Frequency  [1=daily | 2=weekly | 3=monthly]: ").strip()
    price_choice = input("Price type [1=open | 2=high | 3=low | 4=close | 5=volume]: ").strip()
    k           = float(input("Anomaly threshold (# std deviations, e.g. 2): ").strip())
    date_input  = input("Date range YYYY-MM-DD YYYY-MM-DD: ").strip().split()

    if len(date_input) != 2:
        print("[ERROR] Please enter exactly two dates separated by a space.")
        return

    start_date, end_date = date_input
    freq_key, _ = FREQ_MAP.get(freq_choice, FREQ_MAP["1"])
    price_key   = PRICE_KEYS.get(price_choice, PRICE_KEYS["4"])
    apikey      = os.getenv("ALPHAVANTAGE_API_KEY", "demo")

    print(f"\nFetching {freq_key} data for {symbol} ({start_date} → {end_date})...")
    raw_data = download_prices(symbol, start_date, end_date, freq_key, apikey)

    if not raw_data:
        print("No data retrieved. Exiting.")
        return

    prices = {}
    for date, entry in raw_data.items():
        try:
            prices[date] = float(entry[price_key])
        except (KeyError, ValueError):
            continue

    if not prices:
        print(f"[ERROR] Price key '{price_key}' not found in API response.")
        return

    mean, std_dev = compute_stats(prices)
    anomalies = detect_anomalies(prices, mean, std_dev, k)

    print("\n" + "=" * 40)
    print(f"  Symbol      : {symbol}")
    print(f"  Frequency   : {freq_key}")
    print(f"  Price type  : {price_key}")
    print(f"  Date range  : {start_date} → {end_date}")
    print(f"  Data points : {len(prices)}")
    print(f"  Mean        : {mean:.2f}")
    print(f"  Std Dev     : {std_dev:.2f}")
    print(f"  Threshold   : ±{k} σ")
    print("=" * 40)

    if anomalies:
        print(f"\n⚠  {len(anomalies)} anomal{'y' if len(anomalies) == 1 else 'ies'} detected:\n")
        for date in sorted(anomalies):
            z = (anomalies[date] - mean) / std_dev
            direction = "↑" if anomalies[date] > mean else "↓"
            print(f"  {date}  {direction}  {anomalies[date]:.2f}  (z = {z:+.2f})")
    else:
        print(f"\n✅ No anomalies detected at ±{k}σ threshold.")


if __name__ == "__main__":
    main()
