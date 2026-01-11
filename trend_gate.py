"""
trend_gate.py

Daily Trend Gate — Progress-Based Presentation

Purpose:
Detects CONFIRMED DAILY TRENDS suitable for conservative,
pullback-based, spot-only participation.

This module does NOT trade.
It only evaluates trend structure and readiness.

Uses:
- Daily candles (Coinbase)
- Conservative, multi-stage confirmation
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone

from data_source import Candle, fetch_coinbase_candles


# ============================================================
# Configuration (LOCKED / JUSTIFIED)
# ============================================================

LOOKBACK_DAYS = 8              # Balance between noise & responsiveness
MIN_NET_MOVE_PCT = 4.0         # Minimum expansion to prove intent
MIN_DIRECTIONAL_CLOSES = 5     # Consistency check
MAX_RETRACE_PCT = 50.0         # Disqualify deep structural damage


# ============================================================
# Data structures
# ============================================================

@dataclass
class TrendDecision:
    decision: str
    direction: Optional[str]
    reasons: List[str]
    diagnostics: dict


# ============================================================
# Helpers
# ============================================================

def percent_change(a: float, b: float) -> float:
    return (a - b) / b * 100.0


# ============================================================
# Data fetch
# ============================================================

def fetch_daily_candles() -> List[Candle]:
    return fetch_coinbase_candles(
        granularity=86400,
        lookback_days=30
    )


# ============================================================
# Core evaluation
# ============================================================

def evaluate_trend(candles: List[Candle]) -> TrendDecision:
    if len(candles) < LOOKBACK_DAYS + 1:
        return TrendDecision(
            decision="NO TREND",
            direction=None,
            reasons=["Insufficient daily data"],
            diagnostics={}
        )

    window = candles[-LOOKBACK_DAYS:]
    start_price = window[0].close
    end_price = window[-1].close

    net_move_pct = percent_change(end_price, start_price)
    direction = "UP" if net_move_pct > 0 else "DOWN"

    # --------------------------------------------------------
    # Directional closes
    # --------------------------------------------------------

    directional_closes = 0
    for i in range(1, len(window)):
        if direction == "UP" and window[i].close > window[i - 1].close:
            directional_closes += 1
        if direction == "DOWN" and window[i].close < window[i - 1].close:
            directional_closes += 1

    # --------------------------------------------------------
    # Pullback detection
    # --------------------------------------------------------

    pullback_observed = False
    pullback_failed = False
    expansion_origin = window[0].close

    for i in range(1, len(window)):
        prev = window[i - 1]
        cur = window[i]

        if direction == "UP" and cur.close < prev.close:
            pullback_observed = True
            if cur.low > expansion_origin:
                pullback_failed = True

        if direction == "DOWN" and cur.close > prev.close:
            pullback_observed = True
            if cur.high < expansion_origin:
                pullback_failed = True

    # --------------------------------------------------------
    # Retracement depth
    # --------------------------------------------------------

    peak = max(c.high for c in window)
    trough = min(c.low for c in window)
    retrace_pct = abs(percent_change(trough, peak))

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    confirmed = (
        abs(net_move_pct) >= MIN_NET_MOVE_PCT
        and directional_closes >= MIN_DIRECTIONAL_CLOSES
        and pullback_observed
        and pullback_failed
        and retrace_pct <= MAX_RETRACE_PCT
    )

    decision = "TREND CONFIRMED" if confirmed else "NO TREND"

    diagnostics = {
        "direction": direction,
        "price_then": start_price,
        "price_now": end_price,
        "net_move_pct": net_move_pct,
        "directional_closes": directional_closes,
        "pullback_observed": pullback_observed,
        "pullback_failed": pullback_failed,
    }

    return TrendDecision(
        decision=decision,
        direction=direction if confirmed else None,
        reasons=[],
        diagnostics=diagnostics
    )


# ============================================================
# Presentation
# ============================================================

def print_trend_progress(decision: TrendDecision):
    d = decision.diagnostics

    print("\nTREND WATCH — PROGRESS CHECK\n")

    print(f"Directional Bias: {d['direction']}")
    print(f"- Last {MIN_DIRECTIONAL_CLOSES} daily closes moved consistently {d['direction'].lower()}")

    print("\nDistance:")
    print(f"- Price {LOOKBACK_DAYS} days ago: ${d['price_then']:.2f}")
    print(f"- Price now:              ${d['price_now']:.2f}")
    print(f"- Net move: {d['net_move_pct']:.2f}% (requires ≥ {MIN_NET_MOVE_PCT:.1f}%)")

    if abs(d["net_move_pct"]) >= MIN_NET_MOVE_PCT:
        print("✓ Sufficient expansion")
    else:
        print("✗ Insufficient expansion")

    print("\nStructure:")
    print(f"- Pullback observed: {'YES' if d['pullback_observed'] else 'NO'}")
    print(f"- Pullback failure:  {'YES' if d['pullback_failed'] else 'NO'}")

    if d["pullback_failed"]:
        print("✓ Trend defended")
    else:
        print("✗ Trend not defended yet")

    print("\nOverall Status:")
    if decision.decision == "TREND CONFIRMED":
        print("- Trend structure complete")
        print("- Action: PREPARE TREND PULLBACK TRADE (SPOT)")
    else:
        print("- Early directional drift")
        print("- Trend structure incomplete")
        print("- Action: WAIT")


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    candles = fetch_daily_candles()
    decision = evaluate_trend(candles)

    print(decision.decision)
    if decision.direction:
        print(f"Direction: {decision.direction}")

    print_trend_progress(decision)