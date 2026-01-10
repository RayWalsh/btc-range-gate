# trend_gate.py
"""
Trend Gate

Purpose:
- Detect confirmed directional trends (UP only, spot-safe)
- Conservative, pullback-based logic
- No execution, no signals
"""

from dataclasses import dataclass
from typing import List, Optional
from data_source import Candle, fetch_coinbase_candles


# -----------------------------
# CONFIG (LOCKED PHILOSOPHY)
# -----------------------------

LOOKBACK_DAYS = 10          # evaluation window
MIN_NET_MOVE_PCT = 4.0      # minimum directional expansion
MAX_COUNTER_MOVE_PCT = 1.5  # max allowed pullback against trend
MIN_FAILED_PULLBACKS = 1    # must see at least one failed pullback


# -----------------------------
# DATA STRUCTURES
# -----------------------------

@dataclass
class TrendDecision:
    decision: str                    # "TREND CONFIRMED" or "NO TREND"
    direction: Optional[str]         # "UP" or None
    reasons: List[str]
    trend_origin: Optional[float] = None
    trend_high: Optional[float] = None
    net_move_pct: Optional[float] = None


# -----------------------------
# DATA FETCH
# -----------------------------

def fetch_daily_candles() -> List[Candle]:
    """
    Fetch daily candles for trend evaluation.
    """
    return fetch_coinbase_candles(
        granularity=86400,
        lookback_days=LOOKBACK_DAYS + 5  # small buffer
    )


# -----------------------------
# CORE LOGIC
# -----------------------------

def evaluate_trend(candles: List[Candle]) -> TrendDecision:
    reasons: List[str] = []

    if len(candles) < LOOKBACK_DAYS:
        return TrendDecision(
            decision="NO TREND",
            direction=None,
            reasons=["Insufficient candle data"]
        )

    window = candles[-LOOKBACK_DAYS:]

    start_price = window[0].close
    end_price = window[-1].close

    net_move_pct = ((end_price - start_price) / start_price) * 100

    # -----------------------------
    # Directional Expansion Check
    # -----------------------------

    if net_move_pct < MIN_NET_MOVE_PCT:
        reasons.append(
            f"Directional expansion {net_move_pct:.2f}% < {MIN_NET_MOVE_PCT}%"
        )
        return TrendDecision(
            decision="NO TREND",
            direction=None,
            reasons=reasons,
            net_move_pct=net_move_pct
        )

    direction = "UP"

    # -----------------------------
    # Pullback Behaviour Check
    # -----------------------------

    trend_high = max(c.high for c in window)
    trend_origin = window[0].close
    trend_range = trend_high - trend_origin

    failed_pullbacks = 0

    for i in range(1, len(window)):
        candle = window[i]

        pullback_depth = (trend_high - candle.low) / trend_range * 100

        # pullback occurs but does NOT break trend origin
        if 0.5 < pullback_depth <= MAX_COUNTER_MOVE_PCT:
            if candle.close > trend_origin:
                failed_pullbacks += 1

    if failed_pullbacks < MIN_FAILED_PULLBACKS:
        reasons.append(
            f"Failed pullbacks {failed_pullbacks} < {MIN_FAILED_PULLBACKS}"
        )
        return TrendDecision(
            decision="NO TREND",
            direction=None,
            reasons=reasons,
            net_move_pct=net_move_pct
        )

    # -----------------------------
    # TREND CONFIRMED
    # -----------------------------

    return TrendDecision(
        decision="TREND CONFIRMED",
        direction=direction,
        reasons=[],
        trend_origin=trend_origin,
        trend_high=trend_high,
        net_move_pct=net_move_pct
    )


# -----------------------------
# PUBLIC ENTRY POINT
# -----------------------------

def trend_gate_decision() -> TrendDecision:
    candles = fetch_daily_candles()
    decision = evaluate_trend(candles)

    # Console diagnostics (safe for automation)
    if decision.decision == "NO TREND":
        print("NO TREND")
        for r in decision.reasons:
            print(f"- {r}")
        if decision.net_move_pct is not None:
            print(f"- Net move over {LOOKBACK_DAYS}d: {decision.net_move_pct:.2f}%")

    else:
        print("TREND CONFIRMED (UP)")
        print(f"- Net move over {LOOKBACK_DAYS}d: {decision.net_move_pct:.2f}%")
        print(f"- Trend origin: {decision.trend_origin:,.0f}")
        print(f"- Trend high: {decision.trend_high:,.0f}")

    return decision


# -----------------------------
# STANDALONE TEST
# -----------------------------

if __name__ == "__main__":
    trend_gate_decision()