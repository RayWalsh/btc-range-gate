# range_gate.py
"""
BTC Range Gate v1

Answers one question only:
"Is BTC currently in a valid sideways range suitable for range trading?"
"""

from dataclasses import dataclass
from typing import List, Tuple
import requests

import config


BINANCE_URL = "https://api.binance.com/api/v3/klines"


@dataclass
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float


@dataclass
class RangeDecision:
    decision: str
    reasons: List[str]


def fetch_candles(limit: int = 80) -> List[Candle]:
    params = {
        "symbol": config.SYMBOL,
        "interval": config.INTERVAL,
        "limit": limit
    }

    r = requests.get(BINANCE_URL, params=params, timeout=10)
    r.raise_for_status()

    data = r.json()
    candles = []

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


def percent_change(a: float, b: float) -> float:
    return (a - b) / b * 100.0


def evaluate_window(candles: List[Candle], days: int) -> Tuple[bool, List[str]]:
    reasons = []
    needed = days * config.CANDLES_PER_DAY
    window = candles[-needed:]

    highs = [c.high for c in window]
    lows = [c.low for c in window]
    closes = [c.close for c in window]

    upper = max(highs)
    lower = min(lows)

    range_width_pct = (upper - lower) / lower * 100

    if range_width_pct < config.MIN_RANGE_WIDTH_PCT:
        reasons.append(f"Range width {range_width_pct:.2f}% < {config.MIN_RANGE_WIDTH_PCT}%")

    inside = sum(1 for c in window if lower <= c.close <= upper)
    inside_pct = inside / len(window) * 100

    if inside_pct < config.MIN_CLOSES_INSIDE_PCT:
        reasons.append(f"Closes inside range {inside_pct:.1f}% < {config.MIN_CLOSES_INSIDE_PCT}%")

    upper_near = upper * (1 - config.PROXIMITY_PCT / 100)
    upper_rejections = sum(
        1 for c in window
        if c.high >= upper_near and c.close < upper and c.close >= upper_near
    )

    if upper_rejections < config.MIN_REJECTIONS:
        reasons.append(f"Upper rejections {upper_rejections} < {config.MIN_REJECTIONS}")

    lower_near = lower * (1 + config.PROXIMITY_PCT / 100)
    lower_bounces = sum(
        1 for c in window
        if c.low <= lower_near and c.close > lower and c.close <= lower_near
    )

    if lower_bounces < config.MIN_BOUNCES:
        reasons.append(f"Lower bounces {lower_bounces} < {config.MIN_BOUNCES}")

    recent = window[-config.CANDLES_PER_DAY * 2:]
    net_move = abs(percent_change(recent[-1].close, recent[0].close))

    if net_move > config.TREND_EXPANSION_PCT:
        reasons.append(
            f"Recent 2d move {net_move:.2f}% > {config.TREND_EXPANSION_PCT}%"
        )

    return (len(reasons) == 0), reasons


def range_gate_decision() -> RangeDecision:
    candles = fetch_candles()

    min_needed = config.LOOKBACK_DAYS_MAX * config.CANDLES_PER_DAY
    if len(candles) < min_needed:
        return RangeDecision(
            "NO RANGE",
            ["Insufficient candle data"]
        )

    for days in range(config.LOOKBACK_DAYS_MIN, config.LOOKBACK_DAYS_MAX + 1):
        valid, reasons = evaluate_window(candles, days)
        if valid:
            return RangeDecision(
                "RANGE VALID",
                [f"Valid {days}-day range detected"]
            )

    return RangeDecision(
        "NO RANGE",
        ["No valid 7–10 day range window found"]
    )


if __name__ == "__main__":
    decision = range_gate_decision()
    print(decision.decision)
    for r in decision.reasons:
        print(f"- {r}")