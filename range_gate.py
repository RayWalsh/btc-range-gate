# range_gate.py
"""
BTC Range Gate v1

Purpose:
Answers ONE question only:

"Is BTC currently in a valid sideways range suitable for range trading?"

Adds a descriptive REGIME LABEL for human interpretation.
Rules are locked in config.py.
This module performs NO trading.
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
class RangeDecision:
    decision: str
    reasons: List[str]


# ============================================================
# Data fetch
# ============================================================

def fetch_candles(limit: int = 80) -> List[Candle]:
    params = {
        "symbol": config.SYMBOL,
        "interval": config.INTERVAL,
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
# Core evaluation logic
# ============================================================

def evaluate_window(candles: List[Candle], days: int) -> Tuple[bool, List[str]]:
    """
    Evaluates whether the most recent <days> window satisfies
    ALL locked range conditions.

    Returns:
        (is_valid, diagnostics_and_failures)
    """

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
# Regime classification (DESCRIPTIVE ONLY)
# ============================================================

def classify_regime(diagnostics: List[str], decision: str) -> str:
    """
    Human-readable market regime label.
    Does NOT affect trading logic.
    """

    if decision == "RANGE VALID":
        return "VALID_RANGE"

    metrics = {}
    for d in diagnostics:
        if ":" in d:
            k, v = d.split(":", 1)
            metrics[k.strip()] = v.strip()

    closes_inside = float(metrics.get("Closes inside", "0").replace("%", ""))
    range_width = float(metrics.get("Range width", "0").replace("%", ""))
    upper_rej = int(metrics.get("Upper rejections", "0"))
    lower_bnc = int(metrics.get("Lower bounces", "0"))
    recent_move = float(metrics.get("Recent 2d move", "0").replace("%", ""))

    if recent_move > config.TREND_EXPANSION_PCT:
        return "DIRECTIONAL_EXPANSION"

    if (
        closes_inside >= config.MIN_CLOSES_INSIDE_PCT
        and range_width >= config.MIN_RANGE_WIDTH_PCT
        and (upper_rej < config.MIN_REJECTIONS or lower_bnc < config.MIN_BOUNCES)
    ):
        return "CONTAINED_BUT_UNTESTED"

    return "CHAOTIC_OR_UNSTRUCTURED"


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
# Synthetic test (guardrail – NOT executed by default)
# ============================================================

def synthetic_perfect_range_test():
    """
    Synthetic candle set that MUST produce RANGE VALID.
    Used to verify logic integrity (no rule drift).
    """

    candles: List[Candle] = []

    lower = 100.0
    upper = 108.0
    mid = 104.0

    upper_near = upper * (1 - config.PROXIMITY_PCT / 100)
    lower_near = lower * (1 + config.PROXIMITY_PCT / 100)

    for i in range(42):
        candles.append(
            Candle(
                open_time=i,
                open=mid,
                high=mid + 0.3,
                low=mid - 0.3,
                close=mid,
            )
        )

    for i in [8, 14]:
        candles[i] = Candle(
            open_time=i,
            open=upper_near,
            high=upper,
            low=upper_near - 0.5,
            close=upper_near,
        )

    for i in [20, 26]:
        candles[i] = Candle(
            open_time=i,
            open=lower_near,
            high=lower_near + 0.5,
            low=lower,
            close=lower_near,
        )

    for i in range(30, 42):
        candles[i] = Candle(
            open_time=i,
            open=mid,
            high=mid + 0.2,
            low=mid - 0.2,
            close=mid,
        )

    valid, diagnostics = evaluate_window(candles, days=7)

    print("\nSYNTHETIC RANGE TEST")
    print("Expected: RANGE VALID")
    print("Actual:", "RANGE VALID" if valid else "NO RANGE")
    for d in diagnostics:
        print("-", d)


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    decision = range_gate_decision()
    regime = classify_regime(decision.reasons, decision.decision)

    print(decision.decision)
    print(f"Regime: {regime}")
    for reason in decision.reasons:
        print(f"- {reason}")