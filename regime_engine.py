# regime_engine.py
"""
Regime Decision Engine

Purpose:
Combines independent regime gates to determine
what (if any) trading strategy is appropriate today.

This module:
- Does NOT trade
- Does NOT modify gate logic
- Defaults to NO ACTIVE STRATEGY
- Logs one row per run for later review
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone
import csv
import os

import range_gate
import trend_gate


# ============================================================
# Configuration
# ============================================================

LOG_FILE = "regime_log.csv"


# ============================================================
# Data structure
# ============================================================

@dataclass
class RegimeDecision:
    strategy: str
    regime: str
    notes: List[str]
    range_decision: str
    trend_decision: str
    trend_direction: Optional[str]


# ============================================================
# Logging
# ============================================================

def log_decision(decision: RegimeDecision) -> None:
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)

        # Write header once
        if not file_exists:
            writer.writerow([
                "timestamp_utc",
                "strategy",
                "regime",
                "range_decision",
                "trend_decision",
                "trend_direction",
                "notes"
            ])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            decision.strategy,
            decision.regime,
            decision.range_decision,
            decision.trend_decision,
            decision.trend_direction or "",
            " | ".join(decision.notes)
        ])


# ============================================================
# Core decision engine
# ============================================================

def decide_regime() -> RegimeDecision:
    """
    Determines which (if any) strategy is appropriate today.

    Priority order:
    1. RANGE (if validated)
    2. TREND (if confirmed)
    3. Otherwise: NO ACTIVE STRATEGY
    """

    # --------------------------------------------------------
    # 1️⃣ Range gate (4H)
    # --------------------------------------------------------

    range_result = range_gate.range_gate_decision()

    if range_result.decision == "RANGE VALID":
        return RegimeDecision(
            strategy="RANGE TRADING",
            regime="VALID_RANGE (4H)",
            notes=range_result.reasons,
            range_decision=range_result.decision,
            trend_decision="SKIPPED",
            trend_direction=None
        )

    # --------------------------------------------------------
    # 2️⃣ Trend gate (Daily)
    # --------------------------------------------------------

    daily_candles = trend_gate.fetch_daily_candles()
    trend_result = trend_gate.evaluate_trend(daily_candles)

    if trend_result.decision == "TREND CONFIRMED":
        if trend_result.direction == "UP":
            return RegimeDecision(
                strategy="TREND PULLBACK (SPOT)",
                regime="TREND CONFIRMED (DAILY, UP)",
                notes=trend_result.reasons,
                range_decision="NO RANGE",
                trend_decision=trend_result.decision,
                trend_direction="UP"
            )
        else:
            # Downtrend → explicit stand down
            return RegimeDecision(
                strategy="NO ACTIVE STRATEGY",
                regime="TREND CONFIRMED (DAILY, DOWN)",
                notes=[
                    "Daily structure is bearish",
                    "Long exposure discouraged",
                    "Standing down"
                ] + trend_result.reasons,
                range_decision="NO RANGE",
                trend_decision=trend_result.decision,
                trend_direction="DOWN"
            )

    # --------------------------------------------------------
    # 3️⃣ Default: Drift / Transition
    # --------------------------------------------------------

    return RegimeDecision(
        strategy="NO ACTIVE STRATEGY",
        regime="DRIFT / TRANSITION",
        notes=[
            "No validated range",
            "No confirmed trend",
            "Market between regimes",
            "Standing down"
        ],
        range_decision="NO RANGE",
        trend_decision="NO TREND",
        trend_direction=None
    )


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    decision = decide_regime()

    print(f"Strategy: {decision.strategy}")
    print(f"Regime: {decision.regime}")

    for note in decision.notes:
        print(f"- {note}")

    # Append to CSV log
    log_decision(decision)