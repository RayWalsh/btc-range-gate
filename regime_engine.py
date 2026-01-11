"""
regime_engine.py

Daily Regime Decision Engine — Research Logging v2 (Robust)

This version adapts to the *actual* RangeDecision fields
without modifying range_gate.py.
"""

from datetime import datetime, timezone
import csv
import os

import range_gate
import trend_gate


REGIME_LOG_FILE = "regime_log.csv"


CSV_HEADER = [
    "timestamp_utc",
    "strategy",
    "regime",

    # Range gate diagnostics
    "range_decision",
    "range_window_days",
    "range_width_pct",
    "range_closes_inside_pct",
    "range_upper_tests",
    "range_lower_tests",

    # Trend gate diagnostics
    "trend_decision",
    "trend_direction_bias",
    "trend_price_then",
    "trend_price_now",
    "trend_net_move_pct",
    "trend_directional_closes",
    "trend_pullback_observed",
    "trend_pullback_failed",

    # Readiness states
    "range_readiness_state",
    "trend_readiness_state",

    # Future outcomes
    "post_decision_24h_return_pct",
    "post_decision_72h_return_pct",
    "post_decision_7d_return_pct",
]


def ensure_log_file():
    if not os.path.isfile(REGIME_LOG_FILE):
        with open(REGIME_LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)


def decide_regime_and_log():
    timestamp = datetime.now(timezone.utc).isoformat()
    ensure_log_file()

    # ---------------- RANGE GATE ----------------

    range_result = range_gate.range_gate_decision()

    range_decision = range_result.decision
    window_days = getattr(range_result, "window_days", None)
    range_width_pct = getattr(range_result, "range_width_pct", None)
    closes_inside_pct = getattr(range_result, "closes_inside_pct", None)
    upper_tests = getattr(range_result, "upper_rejections", None)
    lower_tests = getattr(range_result, "lower_bounces", None)

    if range_decision == "RANGE VALID":
        range_readiness_state = "RANGE_READY"
    elif window_days is not None and window_days >= 7:
        range_readiness_state = "RANGE_CONTAINED_BUT_UNTESTED"
    else:
        range_readiness_state = "RANGE_NOT_CONTAINED"

    # ---------------- TREND GATE ----------------

    candles = trend_gate.fetch_daily_candles()
    trend_result = trend_gate.evaluate_trend(candles)
    td = trend_result.diagnostics

    if trend_result.decision == "TREND CONFIRMED":
        trend_readiness_state = "TREND_READY"
    elif abs(td.get("net_move_pct", 0)) < 4.0:
        trend_readiness_state = "AWAITING_EXPANSION"
    elif td.get("pullback_observed") and not td.get("pullback_failed"):
        trend_readiness_state = "AWAITING_FAILED_PULLBACK"
    else:
        trend_readiness_state = "EARLY_DIRECTIONAL_DRIFT"

    # ---------------- REGIME HIERARCHY ----------------

    if range_decision == "RANGE VALID":
        strategy = "RANGE TRADING"
        regime = "RANGE"
    elif trend_result.decision == "TREND CONFIRMED":
        strategy = "TREND PULLBACK (SPOT)"
        regime = f"TREND ({trend_result.direction})"
    else:
        strategy = "NO ACTIVE STRATEGY"
        regime = "DRIFT / TRANSITION"

    # ---------------- OUTPUT ----------------

    print(f"\nStrategy: {strategy}")
    print(f"Regime: {regime}")
    trend_gate.print_trend_progress(trend_result)

    # ---------------- LOG ROW ----------------

    row = [
        timestamp,
        strategy,
        regime,

        range_decision,
        window_days,
        range_width_pct,
        closes_inside_pct,
        upper_tests,
        lower_tests,

        trend_result.decision,
        td.get("direction"),
        td.get("price_then"),
        td.get("price_now"),
        td.get("net_move_pct"),
        td.get("directional_closes"),
        td.get("pullback_observed"),
        td.get("pullback_failed"),

        range_readiness_state,
        trend_readiness_state,

        "",
        "",
        "",
    ]

    with open(REGIME_LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow(row)


if __name__ == "__main__":
    decide_regime_and_log()