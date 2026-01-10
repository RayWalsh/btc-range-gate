# trend_gate.py
"""
Daily Trend Gate

Purpose:
Detects CONFIRMED DAILY TRENDS suitable for conservative,
pullback-based, spot-only participation.

This module does NOT trade.
This module does NOT override range_gate.py.
Default outcome is NO TREND.
"""

from dataclasses import dataclass
from typing import List, Tuple
import requests

import config


BINANCE_URL = "https://api.binance.com/api/v3/klines"


# ============================================================
# Data structures
# ============================================================

@dataclass
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float


@dataclass
class TrendDecision:
    decision: str
    direction: str | None
    reasons: List[str]


# ============================================================
# Configuration (locked defaults)
# ============================================================

LOOKBACK_DAYS = 8
MIN_NET_MOVE_PCT = 4.0
MIN_BIASED_CLOSES = 5
MAX_RETRACE_PCT = 50.0


# ============================================================
# Data fetch
# ============================================================

def fetch_daily_candles(limit: int = 30) -> List[Candle]:
    params = {
        "symbol": config.SYMBOL,
        "interval": "1d",
        "limit": limit
    }

    r = requests.get(BINANCE_URL, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()
    candles: List[Candle] = []

    for row in data:
        candles.append(
            Candle(
                open_time=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
            )
        )

    return candles


# ============================================================
# Helpers
# ============================================================

def percent_change(a: float, b: float) -> float:
    return (a - b) / b * 100.0


# ============================================================
# Core trend evaluation
# ============================================================

def evaluate_trend(candles: List[Candle]) -> TrendDecision:
    if len(candles) < LOOKBACK_DAYS + 1:
        return TrendDecision(
            "NO TREND",
            None,
            ["Insufficient daily data"]
        )

    window = candles[-LOOKBACK_DAYS:]
    start_price = window[0].close
    end_price = window[-1].close

    net_move_pct = percent_change(end_price, start_price)

    reasons: List[str] = [
        f"Net move over {LOOKBACK_DAYS}d: {net_move_pct:.2f}%"
    ]

    # --------------------------------------------------------
    # Condition A — Directional expansion
    # --------------------------------------------------------

    if abs(net_move_pct) < MIN_NET_MOVE_PCT:
        return TrendDecision(
            "NO TREND",
            None,
            reasons + ["Directional expansion below threshold"]
        )

    direction = "UP" if net_move_pct > 0 else "DOWN"
    reasons.append(f"Direction: {direction}")

    # --------------------------------------------------------
    # Condition B — Persistence
    # --------------------------------------------------------

    biased_closes = 0
    for i in range(1, len(window)):
        if direction == "UP" and window[i].close > window[i - 1].close:
            biased_closes += 1
        if direction == "DOWN" and window[i].close < window[i - 1].close:
            biased_closes += 1

    reasons.append(f"Biased closes: {biased_closes} / {LOOKBACK_DAYS - 1}")

    if biased_closes < MIN_BIASED_CLOSES:
        return TrendDecision(
            "NO TREND",
            None,
            reasons + ["Directional persistence insufficient"]
        )

    # --------------------------------------------------------
    # Retracement depth check
    # --------------------------------------------------------

    if direction == "UP":
        peak = max(c.high for c in window)
        trough = min(c.low for c in window)
        retrace = percent_change(trough, peak)
    else:
        trough = min(c.low for c in window)
        peak = max(c.high for c in window)
        retrace = percent_change(peak, trough)

    retrace_pct = abs(retrace)
    reasons.append(f"Max retracement: {retrace_pct:.1f}%")

    if retrace_pct > MAX_RETRACE_PCT:
        return TrendDecision(
            "NO TREND",
            None,
            reasons + ["Retracement too deep"]
        )

    # --------------------------------------------------------
    # Condition C — Pullback failure
    # --------------------------------------------------------

    pullback_detected = False
    pullback_failed = False

    expansion_origin = window[0].close

    for i in range(1, len(window)):
        prev = window[i - 1]
        cur = window[i]

        if direction == "UP" and cur.close < prev.close:
            pullback_detected = True
            if cur.low > expansion_origin:
                pullback_failed = True

        if direction == "DOWN" and cur.close > prev.close:
            pullback_detected = True
            if cur.high < expansion_origin:
                pullback_failed = True

    if not pullback_detected:
        return TrendDecision(
            "NO TREND",
            None,
            reasons + ["No pullback occurred (too early)"]
        )

    if not pullback_failed:
        return TrendDecision(
            "NO TREND",
            None,
            reasons + ["Pullbacks succeeded in reclaiming structure"]
        )

    reasons.append("Pullback(s) failed to reverse trend")

    # --------------------------------------------------------
    # Passed all conditions
    # --------------------------------------------------------

    return TrendDecision(
        "TREND CONFIRMED",
        direction,
        reasons
    )


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    candles = fetch_daily_candles()
    decision = evaluate_trend(candles)

    print(decision.decision)
    if decision.direction:
        print(f"Direction: {decision.direction}")

    for r in decision.reasons:
        print(f"- {r}")