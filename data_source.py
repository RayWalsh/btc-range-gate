# data_source.py
"""
Unified OHLC data source using Kraken public API.

Why Kraken:
- Stable
- Automation-safe
- No auth
- No timestamp formatting issues
"""

from dataclasses import dataclass
from typing import List
import requests
import time

KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"

# Kraken interval mapping
INTERVAL_4H = 240   # minutes
INTERVAL_1D = 1440  # minutes


@dataclass
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float


def fetch_kraken_candles(interval_minutes: int, lookback_days: int) -> List[Candle]:
    """
    Fetch OHLC candles from Kraken.

    interval_minutes:
        240  = 4H
        1440 = 1D
    """

    since = int(time.time()) - lookback_days * 86400

    params = {
        "pair": "XBTUSD",
        "interval": interval_minutes,
        "since": since,
    }

    r = requests.get(KRAKEN_URL, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()

    if data.get("error"):
        raise RuntimeError(f"Kraken API error: {data['error']}")

    # Kraken returns a dict keyed by pair name
    ohlc = next(iter(data["result"].values()))

    candles: List[Candle] = []

    for row in ohlc:
        candles.append(
            Candle(
                time=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
            )
        )

    return candles


# Compatibility wrapper (keeps gates unchanged)
def fetch_coinbase_candles(granularity: int, lookback_days: int) -> List[Candle]:
    """
    Compatibility shim so range_gate / trend_gate do not change.
    """

    if granularity == 14400:
        return fetch_kraken_candles(INTERVAL_4H, lookback_days)
    elif granularity == 86400:
        return fetch_kraken_candles(INTERVAL_1D, lookback_days)
    else:
        raise ValueError("Unsupported granularity")