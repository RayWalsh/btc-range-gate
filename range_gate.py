# range_gate.py
"""
BTC Range Gate v1

Purpose:
Answers ONE question only:

"Is BTC currently in a valid sideways range suitable for range trading?"

Uses Coinbase public OHLC data (US-safe).
This module performs NO trading.
"""

from dataclasses import dataclass
from typing import List, Tuple

import config
from data_source import Candle, fetch_coinbase_candles


# ============================================================
# Data structures
# ============================================================

@dataclass
class RangeDecision:
    decision: str
    reasons: List[str]


# ============================================================
# Helpers
# ============================================================

def percent_change(a: float, b: float) -> float:
    return (a - b) / b * 100.0


# ============================================================
# Data fetch (4H candles from Coinbase)
# ============================================================

def fetch_candles() -> List[Candle]:
    # 4H candles, ~10–13 days buffer
    return fetch_coinbase_candles(
        granularity=14400,
        lookback_days=14
    )


# ============================================================
# Core evaluation logic
# ============================================================

def evaluate_window(candles: List[Candle], days: int) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    needed = days * config.CANDLES_PER_DAY
    window = candles[-needed:]

    highs = [c.high for c in window]
    lows = [c.low for c in window]
    closes = [c.close for c in window]

    upper = max(highs)
    lower = min(lows)

    # Rule 5 — Range width
    range_width_pct = (upper - lower) / lower * 100.0
    if range_width_pct < config.MIN_RANGE_WIDTH_PCT:
        reasons.append(
            f"Range width {range_width_pct:.2f}% < {config.MIN_RANGE_WIDTH_PCT}%"
        )

    # Rule 4 — Closes inside range
    inside = sum(1 for c in window if lower <= c.close <= upper)
    inside_pct = inside / len(window) * 100.0
    if inside_pct < config.MIN_CLOSES_INSIDE_PCT:
        reasons.append(
            f"Closes inside range {inside_pct:.1f}% < {config.MIN_CLOSES_INSIDE_PCT}%"
        )

    # Rule 2 — Upper boundary rejections
    upper_near = upper * (1 - config.PROXIMITY_PCT / 100)
    upper_rejections = sum(
        1 for c in window
        if c.high >= upper_near and c.close < upper and c.close >= upper_near
    )
    if upper_rejections < config.MIN_REJECTIONS:
        reasons.append(
            f"Upper rejections {upper_rejections} < {config.MIN_REJECTIONS}"
        )

    # Rule 3 — Lower boundary bounces
    lower_near = lower * (1 + config.PROXIMITY_PCT / 100)
    lower_bounces = sum(
        1 for c in window
        if c.low <= lower_near and c.close > lower and c.close <= lower_near
    )
    if lower_bounces < config.MIN_BOUNCES:
        reasons.append(
            f"Lower bounces {lower_bounces} < {config.MIN_BOUNCES}"
        )

    # Rule 6 — No recent directional expansion
    recent = window[-config.CANDLES_PER_DAY * 2:]  # last ~2 days
    net_move = abs(
        percent_change(recent[-1].close, recent[0].close)
    )
    if net_move > config.TREND_EXPANSION_PCT:
        reasons.append(
            f"Recent 2d move {net_move:.2f}% > {config.TREND_EXPANSION_PCT}%"
        )

    diagnostics = [
        f"Range width: {range_width_pct:.2f}%",
        f"Closes inside: {inside_pct:.1f}%",
        f"Upper rejections: {upper_rejections}",
        f"Lower bounces: {lower_bounces}",
        f"Recent 2d move: {net_move:.2f}%",
    ]

    if reasons:
        return False, diagnostics + ["FAILURES:"] + reasons

    return True, diagnostics


# ============================================================
# Public decision function
# ============================================================

def range_gate_decision() -> RangeDecision:
    candles = fetch_candles()

    min_needed = config.LOOKBACK_DAYS_MAX * config.CANDLES_PER_DAY
    if len(candles) < min_needed:
        return RangeDecision(
            "NO RANGE",
            ["Insufficient candle data"]
        )

    last_diagnostics: List[str] = []

    for days in range(config.LOOKBACK_DAYS_MIN, config.LOOKBACK_DAYS_MAX + 1):
        valid, diagnostics = evaluate_window(candles, days)

        if valid:
            return RangeDecision(
                "RANGE VALID",
                [f"Valid {days}-day range detected"] + diagnostics
            )

        last_diagnostics = diagnostics

    return RangeDecision(
        "NO RANGE",
        [f"Window checked: {days} days"] + last_diagnostics
    )


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    decision = range_gate_decision()
    print(decision.decision)
    for reason in decision.reasons:
        print(f"- {reason}")