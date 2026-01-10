# regime_engine.py
"""
Regime Decision Engine

Purpose:
- Orchestrate range and trend regime gates
- Enforce strict hierarchy:
    RANGE > TREND > NO TRADE
- Print human-readable regime decision
- Suggest numeric trade plans (text-only)
- Log regime state daily
- Log trade plans only when permitted

This module:
- DOES NOT execute trades
- DOES NOT generate signals
- DOES NOT optimise parameters
"""

from datetime import datetime, timezone
import csv
import os

import range_gate
import trend_gate
from trade_plan import (
    generate_range_trade_plan,
    generate_trend_trade_plan,
    log_trade_plan,
)


# ============================================================
# FILES
# ============================================================

REGIME_LOG_FILE = "regime_log.csv"


# ============================================================
# REGIME DECISION
# ============================================================

def decide_regime():
    """
    Determine the current market regime and allowed strategy.
    """

    range_result = range_gate.range_gate_decision()
    trend_result = trend_gate.trend_gate_decision()

    # -----------------------------
    # Hierarchy
    # -----------------------------

    if range_result.decision == "RANGE VALID":
        strategy = "RANGE TRADING"
        regime = "RANGE"
        reasons = ["Validated sideways range"]

    elif trend_result.decision == "TREND CONFIRMED" and trend_result.direction == "UP":
        strategy = "TREND PULLBACK"
        regime = "TREND_UP"
        reasons = ["Confirmed directional trend with pullback behaviour"]

    else:
        strategy = "NO ACTIVE STRATEGY"
        regime = "DRIFT / TRANSITION"
        reasons = [
            "No validated range",
            "No confirmed trend",
            "Market between regimes",
            "Standing down",
        ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "regime": regime,
        "reasons": reasons,
        "range_result": range_result,
        "trend_result": trend_result,
    }


# ============================================================
# LOGGING
# ============================================================

def append_regime_log(decision: dict):
    """
    Append daily regime decision to regime_log.csv
    """

    file_exists = os.path.isfile(REGIME_LOG_FILE)

    with open(REGIME_LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp_utc",
                "strategy",
                "regime",
            ])

        writer.writerow([
            decision["timestamp"],
            decision["strategy"],
            decision["regime"],
        ])


# ============================================================
# OUTPUT + TRADE PLAN LOGGING
# ============================================================

def print_and_log_decision(decision: dict):
    """
    Print regime decision and, when allowed, suggest and log trade plans.
    """

    print(f"Strategy: {decision['strategy']}")
    print(f"Regime: {decision['regime']}")

    for r in decision["reasons"]:
        print(f"- {r}")

    print("")

    # -----------------------------
    # RANGE TRADE PLAN
    # -----------------------------

    if decision["strategy"] == "RANGE TRADING":
        plan = generate_range_trade_plan(decision["range_result"])

        print("STRATEGY SUGGESTION: RANGE TRADING (MEAN REVERSION)")
        print("")

        for key, value in plan.items():
            if key in ["strategy", "regime", "notes"]:
                continue
            print(f"- {key.replace('_', ' ').title()}: {value:,.0f}")

        print(f"- Notes: {plan['notes']}")

        # Spot reference price = last close inside range
        spot_price = decision["range_result"].last_close
        log_trade_plan(plan, spot_price)

    # -----------------------------
    # TREND TRADE PLAN
    # -----------------------------

    elif decision["strategy"] == "TREND PULLBACK":
        plan = generate_trend_trade_plan(decision["trend_result"])

        print("STRATEGY SUGGESTION: TREND PULLBACK (SPOT)")
        print("")

        for key, value in plan.items():
            if key in ["strategy", "regime", "notes"]:
                continue
            print(f"- {key.replace('_', ' ').title()}: {value:,.0f}")

        print(f"- Notes: {plan['notes']}")

        # Spot reference price = most recent trend high
        spot_price = decision["trend_result"].trend_high
        log_trade_plan(plan, spot_price)


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    decision = decide_regime()
    print_and_log_decision(decision)
    append_regime_log(decision)


if __name__ == "__main__":
    main()